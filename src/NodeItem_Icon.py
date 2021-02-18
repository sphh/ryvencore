from PySide2.QtCore import QSize, QRectF, QPointF, QSizeF
from PySide2.QtGui import QPixmap, QImage, QPainter, QIcon, QPicture
from PySide2.QtWidgets import QGraphicsPixmapItem, QGraphicsWidget, QGraphicsLayoutItem


class NodeItem_Icon(QGraphicsWidget):
    def __init__(self, node, node_item):
        super().__init__(parent=node_item)

        if node.style == 'extended':
            self.size = QSize(20, 20)
        else:
            self.size = QSize(50, 50)

        self.setGraphicsItem(self)

        image = QImage(node.icon)
        self.pixmap = QPixmap.fromImage(image)


    def boundingRect(self):
        return QRectF(QPointF(0, 0), self.size)

    def setGeometry(self, rect):
        self.prepareGeometryChange()
        QGraphicsLayoutItem.setGeometry(self, rect)
        self.setPos(rect.topLeft())

    def sizeHint(self, which, constraint=...):
        return QSizeF(self.size.width(), self.size.height())


    def paint(self, painter, option, widget=None):

        # doesn't work: ...
        # painter.setRenderHint(QPainter.Antialiasing, True)
        # painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        # painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        painter.drawPixmap(
            0, 0,
            self.size.width(), self.size.height(),
            self.pixmap
        )