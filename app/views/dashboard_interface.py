# coding: utf-8
import math
from PyQt5.QtCore import Qt, QRectF, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QFontMetrics, QPainterPath
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                              QScrollArea, QFrame, QSizePolicy)

from qfluentwidgets import (SimpleCardWidget, SubtitleLabel, BodyLabel,
                            TitleLabel, CaptionLabel, setFont,
                            FluentIcon as FIF, SmoothScrollArea)

from ..models.stats import StatsModel
from ..common.signal_bus import signal_bus


# ── Chart Colors ──
_COLORS = [
    QColor('#0078D4'), QColor('#00B294'), QColor('#E74856'),
    QColor('#FFB900'), QColor('#8764B8'), QColor('#00CC6A'),
    QColor('#F7630C'), QColor('#CA5010'),
]

_PAYMENT_NAMES = {
    'cash': '现金',
    'wechat': '微信',
    'alipay': '支付宝',
}


class BarChartWidget(QWidget):
    """Simple bar chart drawn with QPainter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # list of {'label': str, 'value': float}
        self._title = ''
        self.setMinimumHeight(200)

    def setData(self, data, title=''):
        self._data = data
        self._title = title
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        margin_l, margin_r, margin_t, margin_b = 50, 15, 30, 50
        chart_w = w - margin_l - margin_r
        chart_h = h - margin_t - margin_b

        # Title
        if self._title:
            painter.setPen(QColor('#333'))
            painter.setFont(QFont(self.font().family(), 11, QFont.Bold))
            painter.drawText(QRectF(0, 5, w, 25), Qt.AlignCenter, self._title)

        max_val = max((d['value'] for d in self._data), default=1) or 1
        n = len(self._data)
        bar_w = max(20, min(50, (chart_w - 10 * n) / n))
        gap = (chart_w - bar_w * n) / (n + 1)

        # Y axis labels
        painter.setFont(QFont(self.font().family(), 9))
        painter.setPen(QColor('#999'))
        for i in range(5):
            y = margin_t + chart_h - (chart_h * i / 4)
            val = max_val * i / 4
            label = self._format_value(val)
            painter.drawText(QRectF(0, y - 8, margin_l - 5, 16),
                             Qt.AlignRight | Qt.AlignVCenter, label)
            painter.setPen(QPen(QColor('#e0e0e0'), 1, Qt.DashLine))
            painter.drawLine(int(margin_l), int(y),
                             int(w - margin_r), int(y))
            painter.setPen(QColor('#999'))

        # Bars
        for i, d in enumerate(self._data):
            x = margin_l + gap + i * (bar_w + gap)
            bar_h = (d['value'] / max_val) * chart_h if max_val else 0
            y = margin_t + chart_h - bar_h

            color = _COLORS[i % len(_COLORS)]
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)

            path = QPainterPath()
            r = min(4, bar_w / 4)
            rect = QRectF(x, y, bar_w, bar_h)
            path.addRoundedRect(rect, r, r)
            painter.drawPath(path)

            # X label
            painter.setPen(QColor('#666'))
            painter.setFont(QFont(self.font().family(), 8))
            fm = QFontMetrics(painter.font())
            elided = fm.elidedText(d['label'], Qt.ElideRight, int(bar_w + gap - 2))
            painter.drawText(
                QRectF(x - gap / 2, margin_t + chart_h + 5,
                       bar_w + gap, 40),
                Qt.AlignHCenter | Qt.AlignTop, elided)

        painter.end()

    @staticmethod
    def _format_value(val):
        if val >= 10000:
            return '{:.1f}w'.format(val / 10000)
        if val >= 1000:
            return '{:.1f}k'.format(val / 1000)
        return '{:.0f}'.format(val)


class PieChartWidget(QWidget):
    """Simple pie/donut chart drawn with QPainter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []  # list of {'label': str, 'value': float}
        self._title = ''
        self.setMinimumHeight(200)

    def setData(self, data, title=''):
        self._data = data
        self._title = title
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        total = sum(d['value'] for d in self._data) or 1

        # Title
        if self._title:
            painter.setPen(QColor('#333'))
            painter.setFont(QFont(self.font().family(), 11, QFont.Bold))
            painter.drawText(QRectF(0, 5, w, 25), Qt.AlignCenter, self._title)

        # Pie
        pie_size = min(w * 0.5, h - 60)
        pie_x = (w * 0.5 - pie_size) / 2 + 10
        pie_y = 35 + (h - 60 - pie_size) / 2
        pie_rect = QRectF(pie_x, pie_y, pie_size, pie_size)

        start_angle = 90 * 16
        for i, d in enumerate(self._data):
            span = int(d['value'] / total * 360 * 16)
            color = _COLORS[i % len(_COLORS)]
            painter.setBrush(color)
            painter.setPen(QPen(Qt.white, 2))
            painter.drawPie(pie_rect, start_angle, span)
            start_angle += span

        # Donut hole
        hole_size = pie_size * 0.45
        hole_rect = QRectF(
            pie_x + (pie_size - hole_size) / 2,
            pie_y + (pie_size - hole_size) / 2,
            hole_size, hole_size)
        painter.setBrush(self.palette().window().color())
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(hole_rect)

        # Legend on right
        legend_x = w * 0.55
        legend_y = 45
        painter.setFont(QFont(self.font().family(), 9))
        for i, d in enumerate(self._data):
            y = legend_y + i * 22
            if y > h - 10:
                break
            color = _COLORS[i % len(_COLORS)]
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(legend_x, y + 2, 12, 12), 2, 2)

            pct = d['value'] / total * 100
            painter.setPen(QColor('#333'))
            label = '{} ({:.0f}%)'.format(d['label'], pct)
            painter.drawText(QRectF(legend_x + 18, y, w - legend_x - 28, 18),
                             Qt.AlignLeft | Qt.AlignVCenter, label)

        painter.end()


class StatCard(SimpleCardWidget):
    """A small statistics card with icon, title and value."""

    def __init__(self, title, value='0', subtitle='', color='#0078D4', parent=None):
        super().__init__(parent)
        self.setFixedHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(4)

        title_label = CaptionLabel(title)
        title_label.setStyleSheet('color: gray;')
        setFont(title_label, 12)
        layout.addWidget(title_label)

        self._value_label = TitleLabel(str(value))
        self._value_label.setStyleSheet('color: {};'.format(color))
        setFont(self._value_label, 28)
        layout.addWidget(self._value_label)

        self._subtitle_label = CaptionLabel(subtitle)
        self._subtitle_label.setStyleSheet('color: #999;')
        layout.addWidget(self._subtitle_label)

    def setValue(self, value):
        self._value_label.setText(str(value))

    def setSubtitle(self, text):
        self._subtitle_label.setText(text)


class DashboardInterface(QWidget):
    """Dashboard with statistics cards and charts for admin users."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_data()

        signal_bus.transaction_completed.connect(self._load_data)
        signal_bus.product_changed.connect(self._load_data)
        signal_bus.stock_changed.connect(self._load_data)

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = SmoothScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet('QScrollArea { background: transparent; }')

        container = QWidget()
        container.setStyleSheet('QWidget { background: transparent; }')
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)

        # ── Stat Cards Row ──
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.todaySalesCard = StatCard('今日交易笔数', '0',
                                       color='#0078D4')
        self.todayRevenueCard = StatCard('今日营业额', '¥0.00',
                                          color='#00B294')
        self.todayItemsCard = StatCard('今日售出件数', '0',
                                        color='#E74856')
        self.productCard = StatCard('商品总数', '0',
                                     subtitle='库存不足: 0', color='#FFB900')

        cards_layout.addWidget(self.todaySalesCard)
        cards_layout.addWidget(self.todayRevenueCard)
        cards_layout.addWidget(self.todayItemsCard)
        cards_layout.addWidget(self.productCard)

        layout.addLayout(cards_layout)

        # ── Charts Row ──
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(12)

        # Bar chart: 7-day sales
        bar_card = SimpleCardWidget()
        bar_layout = QVBoxLayout(bar_card)
        bar_layout.setContentsMargins(10, 10, 10, 10)
        self.barChart = BarChartWidget()
        bar_layout.addWidget(self.barChart)
        charts_layout.addWidget(bar_card, 3)

        # Pie chart: category sales
        pie_card = SimpleCardWidget()
        pie_layout = QVBoxLayout(pie_card)
        pie_layout.setContentsMargins(10, 10, 10, 10)
        self.pieChart = PieChartWidget()
        pie_layout.addWidget(self.pieChart)
        charts_layout.addWidget(pie_card, 2)

        layout.addLayout(charts_layout)

        # ── Bottom Row: top products + low stock ──
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        # Top products
        top_card = SimpleCardWidget()
        top_layout_inner = QVBoxLayout(top_card)
        top_layout_inner.setContentsMargins(20, 15, 20, 15)
        top_layout_inner.setSpacing(8)

        top_title = SubtitleLabel('热销商品 (近30天)')
        top_layout_inner.addWidget(top_title)

        self.topProductsWidget = QWidget()
        self.topProductsLayout = QVBoxLayout(self.topProductsWidget)
        self.topProductsLayout.setContentsMargins(0, 0, 0, 0)
        self.topProductsLayout.setSpacing(4)
        top_layout_inner.addWidget(self.topProductsWidget)
        top_layout_inner.addStretch()

        bottom_layout.addWidget(top_card, 1)

        # Low stock
        low_card = SimpleCardWidget()
        low_layout_inner = QVBoxLayout(low_card)
        low_layout_inner.setContentsMargins(20, 15, 20, 15)
        low_layout_inner.setSpacing(8)

        low_title = SubtitleLabel('库存预警 (< 10)')
        low_layout_inner.addWidget(low_title)

        self.lowStockWidget = QWidget()
        self.lowStockLayout = QVBoxLayout(self.lowStockWidget)
        self.lowStockLayout.setContentsMargins(0, 0, 0, 0)
        self.lowStockLayout.setSpacing(4)
        low_layout_inner.addWidget(self.lowStockWidget)
        low_layout_inner.addStretch()

        bottom_layout.addWidget(low_card, 1)

        layout.addLayout(bottom_layout)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _load_data(self):
        # Stat cards
        sales = StatsModel.today_sales()
        self.todaySalesCard.setValue(str(sales['count']))
        self.todayRevenueCard.setValue('¥{:.2f}'.format(sales['revenue']))

        items_sold = StatsModel.today_items_sold()
        self.todayItemsCard.setValue(str(items_sold))

        product_info = StatsModel.product_summary()
        self.productCard.setValue(str(product_info['total']))
        self.productCard.setSubtitle(
            '库存不足: {}'.format(product_info['low_stock']))

        # Bar chart: 7-day sales
        daily = StatsModel.sales_last_7_days()
        self.barChart.setData(
            [{'label': d['date'], 'value': d['revenue']} for d in daily],
            title='近7天营业额'
        )

        # Pie chart: category or payment
        cat_sales = StatsModel.category_sales()
        if cat_sales:
            self.pieChart.setData(
                [{'label': c['category'], 'value': c['total']}
                 for c in cat_sales],
                title='近30天分类销售'
            )
        else:
            payment = StatsModel.payment_method_stats()
            self.pieChart.setData(
                [{'label': _PAYMENT_NAMES.get(p['method'], p['method']),
                  'value': p['total']} for p in payment],
                title='支付方式分布'
            )

        # Top products list
        self._clear_layout(self.topProductsLayout)
        top = StatsModel.top_products(8)
        if top:
            for i, p in enumerate(top):
                row = QHBoxLayout()
                rank = CaptionLabel('{}. {}'.format(i + 1, p['name']))
                rank.setStyleSheet('color: #333;')
                qty = CaptionLabel('{}件  ¥{:.0f}'.format(p['quantity'], p['revenue']))
                qty.setStyleSheet('color: #666;')
                row.addWidget(rank, 1)
                row.addWidget(qty)
                self.topProductsLayout.addLayout(row)
        else:
            hint = CaptionLabel('暂无销售数据')
            hint.setStyleSheet('color: gray;')
            self.topProductsLayout.addWidget(hint)

        # Low stock list
        self._clear_layout(self.lowStockLayout)
        low = StatsModel.low_stock_products()
        if low:
            for p in low:
                row = QHBoxLayout()
                name = CaptionLabel(p['name'])
                name.setStyleSheet('color: #333;')
                stock = CaptionLabel('库存: {}'.format(p['stock_quantity']))
                color = '#d32f2f' if p['stock_quantity'] <= 3 else '#E65100'
                stock.setStyleSheet('color: {};'.format(color))
                row.addWidget(name, 1)
                row.addWidget(stock)
                self.lowStockLayout.addLayout(row)
        else:
            hint = CaptionLabel('库存充足')
            hint.setStyleSheet('color: #00B294;')
            self.lowStockLayout.addWidget(hint)

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                DashboardInterface._clear_layout(item.layout())
