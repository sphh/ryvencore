from PySide2.QtWidgets import QGraphicsItem, QMenu, QGraphicsDropShadowEffect
from PySide2.QtCore import Qt, QRectF, QObject
from PySide2.QtGui import QColor

from .NodeObjPort import NodeObjInput, NodeObjOutput
from .NodeItemAction import NodeItemAction
from .NodeItemAnimator import NodeItemAnimator
from .NodeItemWidget import NodeItemWidget
from .PortItem import InputPortItem, OutputPortItem
from .global_tools.MovementEnum import MovementEnum


class NodeItem(QGraphicsItem, QObject):

    def __init__(self, node, params):
        QGraphicsItem.__init__(self)
        QObject.__init__(self)

        self.node = node
        flow, design, config = params
        self.flow = flow
        self.session_design = design
        self.movement_state = None
        self.movement_pos_from = None
        self.painted_once = False
        self.inputs = []
        self.outputs = []
        self.color = QColor(self.node.color)  # manipulated by self.animator

        self.personal_logs = []

        # 'initializing' will be set to False below. It's needed for the ports setup, to prevent shape updating stuff
        self.initializing = True

        # self.temp_state_data = None
        self.init_config = config


        # CONNECT TO NODE
        self.node.updated.connect(self.update)
        self.node.update_shape_triggered.connect(self.update_shape)
        self.node.input_added.connect(self.add_new_input)
        self.node.output_added.connect(self.add_new_output)
        self.node.input_removed.connect(self.remove_input)
        self.node.output_removed.connect(self.remove_output)


        # FLAGS
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)



        # UI
        self.shadow_effect = None
        self.main_widget = None
        if self.node.main_widget_class is not None:
            self.main_widget = self.node.main_widget_class(self.node)
        self.widget = NodeItemWidget(self.node, self)  # QGraphicsWidget(self)

        self.animator = NodeItemAnimator(self)  # needs self.title_label

        # TOOLTIP
        if self.node.description != '':
            self.setToolTip('<html><head/><body><p>'+self.node.description+'</p></body></html>')
        self.setCursor(Qt.SizeAllCursor)

        # DESIGN THEME
        self.session_design.flow_theme_changed.connect(self.update_design)



    def initialize(self):
        """All ports and the main widget get finally created here."""

        # LOADING CONFIG
        if self.init_config is not None:
            # self.setPos(config['position x'], config['position y'])
            # self.setup_ports(self.init_config['inputs'], self.init_config['outputs'])
            if self.main_widget:
                try:
                    self.main_widget.set_data(self.init_config['main widget data'])
                except Exception as e:
                    print('Exception while setting data in', self.title, 'Node\'s main widget:', e,
                          ' (was this intended?)')

            # self.special_actions = self.set_special_actions_data(self.init_config['special actions'])
            # self.temp_state_data = self.init_config['state data']
        # else:
        #     self.setup_ports()


        self.initializing = False

        # No self.update_shape() here because for some reason, the bounding rect hasn't been initialized yet, so
        # self.update_shape() gets called when the item is being drawn the first time (see paint event in NI painter)
        # TODO: change that ^ once there is a solution for this: https://forum.qt.io/topic/117179/force-qgraphicsitem-to-update-immediately-wait-for-update-event

        self.update_design()  # load current design, update QGraphicsItem

        self.update()  # ... not sure if I need that



    # --------------------------------------------------------------------------------------
    # UI STUFF ----------------------------------------


    def node_updated(self):
        if self.session_design.animations_enabled:
            self.animator.start()


    def add_new_input(self, inp: NodeObjInput, pos: int):

        # create item
        inp.item = InputPortItem(inp.node, inp)

        if pos == -1:
            self.inputs.append(inp.item)
            self.widget.add_input_to_layout(inp.item)
        else:
            self.inputs.insert(pos, inp.item)
            self.widget.insert_input_into_layout(pos, inp.item)

        if not self.initializing:
            self.update_shape()
            self.update()

    def remove_input(self, inp: NodeObjInput):
        item = inp.item

        # for some reason, I have to remove all widget items manually from the scene too. setting the items to
        # ownedByLayout(True) does not work, I don't know why.
        self.scene().removeItem(item.pin)
        self.scene().removeItem(item.label)
        if item.proxy is not None:
            self.scene().removeItem(item.proxy)

        self.inputs.remove(item)
        self.widget.remove_input_from_layout(item)

        if not self.initializing:
            self.update_shape()
            self.update()

    def add_new_output(self, out: NodeObjOutput, pos: int):

        # create item
        out.item = OutputPortItem(out.node, out)

        if pos == -1:
            self.outputs.append(out.item)
            self.widget.add_output_to_layout(out.item)
        else:
            self.outputs.insert(pos, out.item)
            self.widget.insert_output_into_layout(pos, out.item)

        if not self.initializing:
            self.update_shape()
            self.update()

    def remove_output(self, out: NodeObjOutput):
        item = out.item

        # see remove_input() for info!
        self.scene().removeItem(item.pin)
        self.scene().removeItem(item.label)

        self.outputs.remove(item)
        self.widget.remove_output_from_layout(item)

        if not self.initializing:
            self.update_shape()
            self.update()


    def update_shape(self):
        self.widget.update_shape()
        self.update_conn_pos()
        self.flow.viewport().update()

    def update_design(self):
        """Loads the shadow effect option and causes redraw with active theme."""

        if self.session_design.node_item_shadows_enabled:
            self.shadow_effect = QGraphicsDropShadowEffect()
            self.shadow_effect.setXOffset(12)
            self.shadow_effect.setYOffset(12)
            self.shadow_effect.setBlurRadius(20)
            self.shadow_effect.setColor(QColor('#2b2b2b'))
            self.setGraphicsEffect(self.shadow_effect)
        else:
            self.setGraphicsEffect(None)

        self.widget.update()
        self.animator.reload_values()

        QGraphicsItem.update(self)

    def boundingRect(self):
        # remember: (0, 0) shall be the NI's center!
        rect = QRectF()
        w = self.widget.layout().geometry().width()
        h = self.widget.layout().geometry().height()
        rect.setLeft(-w/2)
        rect.setTop(-h/2)
        rect.setWidth(w)
        rect.setHeight(h)
        return rect

    #   PAINTING
    def paint(self, painter, option, widget=None):
        """All painting is done by NodeItemPainter"""

        # in order to access a meaningful geometry of GraphicsWidget contents in update_shape(), the paint event
        # has to be called once. See here:
        # https://forum.qt.io/topic/117179/force-qgraphicsitem-to-update-immediately-wait-for-update-event/4
        if not self.painted_once:

            # ok, quick notice. Since I am using a NodeItemWidget, calling self.update_design() here (again)
            # leads to a QT crash without error, which is really strange. Calling update_design multiple times
            # principally isn't a problem, but, for some reason, here it leads to a crash in QT. It's not necessary
            # anymore, so I just removed it.
            # self.update_design()

            self.update_shape()
            self.update_conn_pos()

        self.session_design.flow_theme.node_item_painter.paint_NI(
            design_style=self.node.style,
            painter=painter,
            option=option,
            c=self.color,
            w=self.boundingRect().width(),
            h=self.boundingRect().height(),
            bounding_rect=self.boundingRect(),
            title_rect=self.widget.title_label.boundingRect()
        )

        self.painted_once = True

    def get_context_menu(self):
        menu = QMenu(self.flow)

        for a in self.get_actions(self.node.get_extended_default_actions(), menu):  # menu needed for 'parent'
            if type(a) == NodeItemAction:
                menu.addAction(a)
            elif type(a) == QMenu:
                menu.addMenu(a)

        menu.addSeparator()

        actions = self.get_actions(self.node.special_actions, menu)
        for a in actions:  # menu needed for 'parent'
            if type(a) == NodeItemAction:
                menu.addAction(a)
            elif type(a) == QMenu:
                menu.addMenu(a)

        return menu

    def itemChange(self, change, value):
        """This method ensures that all connections, selection borders etc. that get drawn in the Flow are constantly
        redrawn during a NI drag. Also updates the positions of connections"""

        if change == QGraphicsItem.ItemPositionChange:
            if self.session_design.performance_mode == 'pretty':
                self.flow.viewport().update()
            if self.movement_state == MovementEnum.mouse_clicked:
                self.movement_state = MovementEnum.position_changed

        self.update_conn_pos()

        return QGraphicsItem.itemChange(self, change, value)

    def update_conn_pos(self):
        """Updates the global positions of connections at outputs"""
        for o in self.node.outputs:
            for c in o.connections:
                # c.item.recompute()
                item = self.flow.connection_items[c]
                item.recompute()
        for i in self.node.inputs:
            for c in i.connections:
                # c.item.recompute()
                item = self.flow.connections_items[c]
                item.recompute()

    def hoverEnterEvent(self, event):
        self.widget.title_label.set_NI_hover_state(hovering=True)
        QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        self.widget.title_label.set_NI_hover_state(hovering=False)
        QGraphicsItem.hoverLeaveEvent(self, event)

    def mousePressEvent(self, event):
        """Used for Moving-Commands in Flow - may be replaced later with a nicer determination of a moving action."""
        if event.button() == Qt.LeftButton:
            self.movement_state = MovementEnum.mouse_clicked
            self.movement_pos_from = self.pos()
        return QGraphicsItem.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        """Used for Moving-Commands in Flow - may be replaced later with a nicer determination of a moving action."""
        if self.movement_state == MovementEnum.position_changed:
            self.flow.selected_components_moved(self.pos() - self.movement_pos_from)
        self.movement_state = None
        return QGraphicsItem.mouseReleaseEvent(self, event)

    # ACTIONS
    def get_actions(self, actions_dict, menu):
        actions = []

        for k in actions_dict:
            v_dict = actions_dict[k]
            try:
                method = v_dict['method']
                data = None
                try:
                    data = v_dict['data']
                except KeyError:
                    pass
                action = NodeItemAction(text=k, method=method, menu=menu, data=data)
                if self.flow.session.threaded:
                    action.triggered_with_data__thread.connect(self.flow.thread_interface.trigger_node_action)
                    action.triggered_without_data__thread.connect(self.flow.thread_interface.trigger_node_action)
                else:
                    action.triggered_with_data.connect(method)  # see NodeItemAction for explanation
                    action.triggered_without_data.connect(method)  # see NodeItemAction for explanation

                actions.append(action)
            except KeyError:
                action_menu = QMenu(k, menu)
                sub_actions = self.get_actions(v_dict, action_menu)
                for a in sub_actions:
                    action_menu.addAction(a)
                actions.append(action_menu)

        return actions

    def complete_config(self, node_config):
        # add input widgets config
        for i in range(len(node_config['inputs'])):
            input_cfg = node_config['inputs'][i]
            inp_item = self.inputs[i]

            if inp_item.port.type_ == 'data':
                if inp_item.widget:
                    input_cfg['has widget'] = True
                    input_cfg['widget name'] = inp_item.widget_name
                    input_cfg['widget data'] = inp_item.widget.get_data()
                    input_cfg['widget position'] = inp_item.port.widget_pos
                else:
                    input_cfg['has widget'] = False
                node_config['inputs'][i] = input_cfg

        # add item properties
        node_config['pos x'] = self.pos().x()
        node_config['pos y'] = self.pos().y()
        node_config['main widget data'] = self.main_widget.get_data()

        return node_config