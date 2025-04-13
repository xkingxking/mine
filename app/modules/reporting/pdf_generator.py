# 确保中文字体文件存在并正确注册
import os
import io
import re
import datetime
import logging
import math
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, Flowable, Frame, PageTemplate, NextPageTemplate,
    HRFlowable
)
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Circle, Wedge, Polygon
from reportlab.graphics.charts.barcharts import VerticalBarChart, HorizontalBarChart
from reportlab.graphics.charts.linecharts import LineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.widgets.markers import makeMarker

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 自定义颜色主题 - 专业配色方案
COLOR_THEME = {
    'primary': colors.HexColor('#1F4E79'),       # 深蓝色 - 主色调
    'secondary': colors.HexColor('#2E75B6'),     # 蓝色 - 次色调
    'tertiary': colors.HexColor('#5B9BD5'),      # 浅蓝色 - 第三色调
    'accent': colors.HexColor('#ED7D31'),        # 橙色 - 强调色
    'accent_light': colors.HexColor('#F8CBAD'),  # 浅橙色
    'success': colors.HexColor('#70AD47'),       # 绿色 - 成功色
    'warning': colors.HexColor('#FFC000'),       # 黄色 - 警告色
    'error': colors.HexColor('#C00000'),         # 红色 - 错误色
    'background': colors.HexColor('#F2F2F2'),    # 浅灰色 - 背景色
    'text': colors.HexColor('#333333'),          # 黑色 - 正文文本色
    'text_light': colors.HexColor('#666666'),    # 灰色 - 浅色文本
    'table_header': colors.HexColor('#4472C4'),  # 表格头部
    'table_alt_row': colors.HexColor('#E6F0FF'),  # 表格交替行
    
    # 增加新的评分等级颜色
    'grade_a': colors.HexColor('#70AD47'),       # A级 - 绿色
    'grade_b': colors.HexColor('#92D050'),       # B级 - 浅绿色
    'grade_c': colors.HexColor('#FFC000'),       # C级 - 黄色
    'grade_d': colors.HexColor('#ED7D31'),       # D级 - 橙色
    'grade_f': colors.HexColor('#C00000'),       # F级 - 红色
    
    # 饼图颜色
    'pie_colors': [
        colors.HexColor('#4472C4'),  # 蓝色
        colors.HexColor('#70AD47'),  # 绿色
        colors.HexColor('#FFC000'),  # 黄色
        colors.HexColor('#ED7D31'),  # 橙色
        colors.HexColor('#5B9BD5'),  # 浅蓝色
        colors.HexColor('#A5A5A5'),  # 灰色
        colors.HexColor('#6F6F6F'),  # 深灰色
        colors.HexColor('#8FAADC'),  # 淡蓝色
    ],
    
    # 雷达图颜色
    'radar_fill': colors.HexColor('#4472C4'),  # 填充色
    'radar_line': colors.HexColor('#2E75B6'),  # 线条色
    'radar_grid': colors.HexColor('#CCCCCC'),  # 网格色
}

# 定义标准的评分等级
SCORE_GRADES = [
    {'min': 0.9, 'grade': 'A', 'color': COLOR_THEME['grade_a'], 'description': '优秀'},
    {'min': 0.8, 'grade': 'B', 'color': COLOR_THEME['grade_b'], 'description': '良好'},
    {'min': 0.7, 'grade': 'C', 'color': COLOR_THEME['grade_c'], 'description': '一般'},
    {'min': 0.6, 'grade': 'D', 'color': COLOR_THEME['grade_d'], 'description': '待改进'},
    {'min': 0.0, 'grade': 'F', 'color': COLOR_THEME['grade_f'], 'description': '不及格'}
]

def get_score_grade(score):
    """根据分数获取等级和对应的颜色"""
    for grade_info in SCORE_GRADES:
        if score >= grade_info['min']:
            return grade_info['grade'], grade_info['color']
    return 'F', COLOR_THEME['grade_f']  # 默认返回F级

def get_score_description(score):
    """根据分数获取等级描述"""
    for grade_info in SCORE_GRADES:
        if score >= grade_info['min']:
            return grade_info['description']
    return '不及格'  # 默认返回不及格

# 添加一个函数来查找字体文件
def find_font_file(font_name):
    """
    尝试在多个可能的位置查找字体文件
    """
    possible_paths = [
        # 当前目录下的 fonts 文件夹
        os.path.join(os.path.dirname(__file__), 'fonts', font_name),
        # 系统字体目录 (Windows)
        os.path.join('C:\\', 'Windows', 'Fonts', font_name),
        # 系统字体目录 (Linux)
        os.path.join('/usr', 'share', 'fonts', 'truetype', font_name),
        # Mac OS 字体目录
        os.path.join('/Library', 'Fonts', font_name),
        os.path.join(os.path.expanduser('~'), 'Library', 'Fonts', font_name),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.debug(f"找到字体文件: {path}")
            return path
    
    logger.warning(f"未找到字体文件: {font_name}")
    return None

# 尝试注册中文字体
def register_chinese_font():
    """
    注册中文字体，尝试多个常见中文字体
    """
    # 尝试注册常用中文字体
    chinese_fonts = ['SimHei.ttf', 'simkai.ttf', 'simfang.ttf', 'simsun.ttc', 'msyh.ttf', 'STKAITI.TTF', 'SIMYOU.TTF', 'FZSTK.TTF', 'SIMLI.TTF', 'STFANGSO.TTF']
    
    for font_file in chinese_fonts:
        font_path = find_font_file(font_file)
        if font_path:
            try:
                font_name = os.path.splitext(font_file)[0]  # 去掉扩展名
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                logger.debug(f"成功注册中文字体: {font_name} ({font_path})")
                return font_name  # 返回成功注册的字体名称
            except Exception as e:
                logger.error(f"注册字体 {font_file} 失败: {str(e)}")
    
    # 如果所有尝试都失败，则创建一个简单的中文字体目录
    try:
        fonts_dir = os.path.join(os.path.dirname(__file__), 'fonts')
        os.makedirs(fonts_dir, exist_ok=True)
        logger.info(f"已创建字体目录: {fonts_dir}，请手动复制中文字体文件到此目录")
    except Exception as e:
        logger.error(f"创建字体目录失败: {str(e)}")
    
    # 如果无法找到中文字体，使用默认的Helvetica
    logger.warning("未找到中文字体，将使用默认的Helvetica字体")
    return None

# 在生成PDF之前调用这个函数
chinese_font = register_chinese_font()

# 自定义Flowable: 页眉页脚
class PageHeaderFooter(object):
    """为每一页添加页眉和页脚"""
    
    def __init__(self, title, logo_path=None, chinese_font=None):
        self.title = title
        self.logo_path = logo_path
        self.chinese_font = chinese_font
    
    def __call__(self, canvas, doc):
        canvas.saveState()
        
        # 设置字体
        font_name = self.chinese_font if self.chinese_font else "Helvetica"
        
        # 添加页眉
        canvas.setFont(font_name, 10)
        canvas.setFillColor(COLOR_THEME['text_light'])
        
        # 添加标题
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 15, self.title)
        
        # 添加日期
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        canvas.drawRightString(doc.width + doc.leftMargin, doc.height + doc.topMargin - 15, date_str)
        
        # 添加页眉分隔线
        canvas.setStrokeColor(COLOR_THEME['tertiary'])
        canvas.line(doc.leftMargin, doc.height + doc.topMargin - 20, 
                    doc.width + doc.leftMargin, doc.height + doc.topMargin - 20)
        
        # 添加页码
        page_num = canvas.getPageNumber()
        text = f"页码 {page_num}"
        canvas.setFont(font_name, 9)
        canvas.drawRightString(
            doc.width + doc.leftMargin, 
            doc.bottomMargin - 15, 
            text
        )
        
        # 添加页脚分隔线
        canvas.setStrokeColor(COLOR_THEME['tertiary'])
        canvas.line(doc.leftMargin, doc.bottomMargin - 5, 
                    doc.width + doc.leftMargin, doc.bottomMargin - 5)
        
        canvas.restoreState()

# 自定义Flowable: 封面
class CoverPage(Flowable):
    """创建PDF报告的封面页"""
    
    def __init__(self, title, logo_path=None, model_info=None, chinese_font=None):
        Flowable.__init__(self)
        self.title = title
        self.logo_path = logo_path
        self.model_info = model_info or {}
        self.chinese_font = chinese_font
        # Don't set fixed dimensions here - will be determined in wrap
    
    def wrap(self, availWidth, availHeight):
        # Tell ReportLab we'll use the available space, but not more
        # This is critical to prevent overflow errors
        self.width = availWidth
        self.height = availHeight
        return (self.width, self.height)
    
    def draw(self):
        # Background - respect available width and height
        padding = 6  # Standard frame padding
        usable_width = self.width - (2 * padding)
        usable_height = self.height - (2 * padding)
        
        # Adjust coordinates to stay within bounds
        self.canv.setFillColor(COLOR_THEME['background'])
        self.canv.roundRect(padding, padding, usable_width, usable_height, 10, fill=1, stroke=0)
        
        # 标题栏背景
        self.canv.setFillColor(COLOR_THEME['primary'])
        self.canv.rect(padding, usable_height - 3*cm + padding, usable_width, 3*cm, fill=1, stroke=0)
        
        # 标题文本
        self.canv.setFillColor(colors.white)
        font_name = self.chinese_font if self.chinese_font else "Helvetica-Bold"
        self.canv.setFont(font_name, 24)
        
        # 绘制标题文本
        title_width = self.canv.stringWidth(self.title, font_name, 24)
        title_x = padding + (usable_width - title_width) / 2
        self.canv.drawString(title_x, usable_height - 1.8*cm + padding, self.title)
        
        # 添加装饰线
        self.canv.setStrokeColor(COLOR_THEME['accent'])
        self.canv.setLineWidth(3)
        self.canv.line(2*cm + padding, usable_height - 3.5*cm + padding, 
                       usable_width - 2*cm + padding, usable_height - 3.5*cm + padding)
        
        # 添加模型信息
        y_position = usable_height - 5*cm + padding
        
        if self.model_info:
            # 添加模型名称
            self.canv.setFillColor(COLOR_THEME['primary'])
            self.canv.setFont(font_name, 18)
            model_name = self.model_info.get('name', '未知模型')
            self.canv.drawString(2*cm + padding, y_position, f"模型名称: {model_name}")
            y_position -= 1.5*cm
            
            # 添加版本信息
            version = self.model_info.get('version', '1.0')
            self.canv.setFont(font_name, 14)
            self.canv.setFillColor(COLOR_THEME['secondary'])
            self.canv.drawString(2*cm + padding, y_position, f"版本: {version}")
            y_position -= 1*cm
            
            # 添加更新时间
            update_date = self.model_info.get('last_update', datetime.datetime.now().isoformat())
            try:
                if isinstance(update_date, str):
                    # 尝试解析ISO格式日期字符串
                    parsed_date = datetime.datetime.fromisoformat(update_date.replace('Z', '+00:00'))
                    formatted_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    formatted_date = update_date
            except (ValueError, TypeError):
                formatted_date = update_date
                
            self.canv.setFont(font_name, 14)
            self.canv.drawString(2*cm + padding, y_position, f"更新时间: {formatted_date}")
            y_position -= 1*cm
            
            # 添加提供商信息
            provider = self.model_info.get('provider', '')
            if provider:
                self.canv.drawString(2*cm + padding, y_position, f"提供商: {provider}")
                y_position -= 1*cm
        
        # 添加报告生成时间
        self.canv.setFillColor(COLOR_THEME['text_light'])
        self.canv.setFont(font_name, 12)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.canv.drawString(2*cm + padding, 2*cm + padding, f"报告生成时间: {current_time}")
        
        # 添加装饰元素 - 底部图形
        self.canv.setFillColor(COLOR_THEME['accent'])
        self.canv.rect(padding, padding, usable_width, 1*cm, fill=1, stroke=0)
        
        # 添加装饰图形 - 右上角
        self.canv.setFillColor(COLOR_THEME['tertiary'])
        self.canv.setStrokeColor(COLOR_THEME['tertiary'])
        self.canv.circle(usable_width - 2*cm + padding, usable_height - 5*cm + padding, 1*cm, fill=1, stroke=0)
        
        # 添加装饰图形 - 左下角
        self.canv.setFillColor(COLOR_THEME['secondary'])
        self.canv.circle(2*cm + padding, 4*cm + padding, 0.8*cm, fill=1, stroke=0)

# 自定义Flowable: 目录
class TableOfContents(Flowable):
    """创建PDF报告的目录页"""
    
    def __init__(self, entries, usable_width, chinese_font=None):
        Flowable.__init__(self)
        self.entries = entries
        # Assume the width passed is the usable width within padding
        self.width = usable_width 
        self.chinese_font = chinese_font
        self.entry_height = 25 # Height per entry
        self.title_height = 40 # Space for title and line
        self.calculated_height = 0 # Will be set in wrap

    def wrap(self, availWidth, availHeight):
        # The width is already the usable width, ensure it fits availWidth
        self.width = min(self.width, availWidth)
        
        # Calculate required height based on entries
        num_entries = len(self.entries)
        required_height = self.title_height + (num_entries * self.entry_height)
        self.calculated_height = required_height

        # Return the dimensions this flowable will occupy
        return (self.width, self.calculated_height)

    def draw(self):
        # Use dimensions calculated in wrap
        current_draw_height = self.calculated_height
        current_draw_width = self.width # This is the usable width

        # Draw relative to Flowable's origin (0,0)

        # Add title
        font_name = self.chinese_font if self.chinese_font else "Helvetica-Bold"
        self.canv.setFont(font_name, 20)
        self.canv.setFillColor(COLOR_THEME['primary'])
        self.canv.drawString(0, current_draw_height - 30, "目录")

        # Add decoration line spanning the usable width
        self.canv.setStrokeColor(COLOR_THEME['secondary'])
        self.canv.setLineWidth(1)
        self.canv.line(0, current_draw_height - 40, current_draw_width, current_draw_height - 40)

        # Add TOC entries
        y_position = current_draw_height - 70
        left_indent = 14
        page_number_x = current_draw_width

        for i, (title, page) in enumerate(self.entries):
            if y_position < 0:
                break

            self.canv.setFont(font_name, 14)
            self.canv.setFillColor(COLOR_THEME['text'])
            self.canv.drawString(left_indent, y_position, title)

            self.canv.setStrokeColor(COLOR_THEME['text_light'])
            self.canv.setDash([1, 2], 0)
            dot_line_y = y_position + 7
            title_width = self.canv.stringWidth(title, font_name, 14)
            page_width = self.canv.stringWidth(str(page), font_name, 14)

            dot_start = left_indent + title_width + 10
            dot_end = page_number_x - page_width - 10

            if dot_start < dot_end:
                self.canv.line(dot_start, dot_line_y, dot_end, dot_line_y)

            self.canv.setDash([], 0)
            self.canv.drawRightString(page_number_x, y_position, str(page))
            y_position -= self.entry_height

# 自定义Flowable: 信息框
class InfoBox(Flowable):
    """创建信息提示框"""
    
    def __init__(self, text, width, boxType="info", chinese_font=None):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        self.boxType = boxType
        self.chinese_font = chinese_font
        
        # 根据文本长度计算高度
        font_name = chinese_font if chinese_font else "Helvetica"
        font_size = 10
        chars_per_line = int(width / 7)  # 大约每个字符7个点
        lines = math.ceil(len(text) / chars_per_line)
        self.height = lines * (font_size + 4) + 20  # 行高+边距
    
    def wrap(self, availWidth, availHeight):
        # 确保不超出可用宽度
        self.width = min(self.width, availWidth)
        return (self.width, self.height)
        
    def draw(self):
        # 不再绘制背景和边框，只显示文本
        font_name = self.chinese_font if self.chinese_font else "Helvetica"
        self.canv.setFont(font_name, 10)
        self.canv.setFillColor(COLOR_THEME['text'])
        
        # 使用简单的文本包装
        text_lines = []
        words = self.text.split()
        current_line = words[0] if words else ""
        
        for word in words[1:]:
            if self.canv.stringWidth(current_line + " " + word, font_name, 10) < (self.width - 30):
                current_line += " " + word
            else:
                text_lines.append(current_line)
                current_line = word
                
        text_lines.append(current_line)  # 添加最后一行
        
        # 绘制文本
        for i, line in enumerate(text_lines):
            y_pos = self.height - 15 - i * 14
            self.canv.drawString(15, y_pos, line)

# 自定义Flowable: 评分表格
class ScoreGradeTable(Flowable):
    """创建评分等级说明表格"""
    
    def __init__(self, width, height, chinese_font=None):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.chinese_font = chinese_font
    
    def draw(self):
        # 设置字体
        font_name = self.chinese_font if self.chinese_font else "Helvetica"
        
        # 创建表格数据
        data = [["等级", "分数", "描述"]]
        for grade_info in SCORE_GRADES:
            min_score = grade_info['min'] * 100
            if min_score == 0:
                score_range = "0-59%"
            else:
                max_score = 100 if min_score >= 90 else (grade_info['min'] + 0.1) * 100 - 1
                score_range = f"{min_score:.0f}-{max_score:.0f}%"
                
            data.append([
                grade_info['grade'],
                score_range,
                grade_info['description']
            ])
        
        # 计算每列宽度
        col_widths = [self.width * 0.2, self.width * 0.3, self.width * 0.5]
        
        # 绘制表格
        x_positions = [0]
        running_width = 0
        for w in col_widths:
            running_width += w
            x_positions.append(running_width)
        
        # 绘制表头
        self.canv.setFont(font_name, 10)
        self.canv.setFillColor(colors.white)
        self.canv.setStrokeColor(COLOR_THEME['primary'])
        
        self.canv.setFillColor(COLOR_THEME['table_header'])
        self.canv.rect(x_positions[0], self.height - 20, col_widths[0], 20, fill=1, stroke=1)
        self.canv.rect(x_positions[1], self.height - 20, col_widths[1], 20, fill=1, stroke=1)
        self.canv.rect(x_positions[2], self.height - 20, col_widths[2], 20, fill=1, stroke=1)
        
        # 绘制表头文字
        self.canv.setFillColor(colors.white)
        self.canv.drawCentredString(x_positions[0] + col_widths[0]/2, self.height - 15, data[0][0])
        self.canv.drawCentredString(x_positions[1] + col_widths[1]/2, self.height - 15, data[0][1])
        self.canv.drawCentredString(x_positions[2] + col_widths[2]/2, self.height - 15, data[0][2])
        
        # 绘制每一行数据
        for i, row in enumerate(data[1:]):
            row_y = self.height - 20 - (i+1) * 20
            grade_color = next((g['color'] for g in SCORE_GRADES if g['grade'] == row[0]), COLOR_THEME['text'])
            
            # 背景色
            if i % 2 == 0:
                self.canv.setFillColor(colors.white)
            else:
                self.canv.setFillColor(COLOR_THEME['table_alt_row'])
                
            # 绘制单元格背景
            self.canv.rect(x_positions[0], row_y, col_widths[0], 20, fill=1, stroke=1)
            self.canv.rect(x_positions[1], row_y, col_widths[1], 20, fill=1, stroke=1)
            self.canv.rect(x_positions[2], row_y, col_widths[2], 20, fill=1, stroke=1)
            
            # 绘制文字
            self.canv.setFillColor(grade_color)
            self.canv.setFont(font_name, 12)
            self.canv.drawCentredString(x_positions[0] + col_widths[0]/2, row_y + 6, row[0])
            
            self.canv.setFillColor(COLOR_THEME['text'])
            self.canv.setFont(font_name, 10)
            self.canv.drawCentredString(x_positions[1] + col_widths[1]/2, row_y + 6, row[1])
            self.canv.drawString(x_positions[2] + 10, row_y + 6, row[2])

# 自定义Flowable: 柱状图
class DomainBarChart(Flowable):
    """创建柱状图显示各领域评分"""
    
    def __init__(self, width, height, scores, domains, chinese_font=None, title=None):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.scores = scores  # 分数列表 (0-1之间)
        self.domains = domains  # 领域名称列表
        self.chinese_font = chinese_font
        self.title = title
    
    def wrap(self, availWidth, availHeight):
        # 确保不超出可用宽度
        self.width = min(self.width, availWidth)
        return (self.width, self.height)
    
    def draw(self):
        if not self.scores or not self.domains:
            return
            
        # 设置图表区域
        margin_left = 80   # 左边距增大以容纳长域名
        margin_right = 20
        margin_top = 30
        margin_bottom = 50 # 底部边距增大以容纳横向的域名标签
        
        chart_width = self.width - margin_left - margin_right
        chart_height = self.height - margin_top - margin_bottom
        
        # 绘制标题
        if self.title:
            font_name = self.chinese_font if self.chinese_font else "Helvetica-Bold"
            self.canv.setFont(font_name, 14)
            self.canv.setFillColor(COLOR_THEME['primary'])
            self.canv.drawCentredString(self.width / 2, self.height - 15, self.title)
        
        # 计算柱子宽度和间距
        num_domains = len(self.scores)
        if num_domains <= 0:
            return
            
        bar_width = min(40, chart_width / (num_domains * 1.5))  # 柱宽不超过40点
        spacing = (chart_width - (bar_width * num_domains)) / (num_domains + 1)
        
        # 绘制Y轴和刻度
        self.canv.setStrokeColor(COLOR_THEME['text'])
        self.canv.setLineWidth(1)
        self.canv.line(margin_left, margin_bottom, margin_left, margin_bottom + chart_height)
        
        # 绘制刻度
        for i in range(6):  # 0%, 20%, 40%, 60%, 80%, 100%
            y = margin_bottom + (i / 5) * chart_height
            self.canv.line(margin_left - 5, y, margin_left, y)
            
            # 绘制横线
            self.canv.setStrokeColor(COLOR_THEME['radar_grid'])
            self.canv.setDash([1, 2], 0)
            self.canv.line(margin_left, y, margin_left + chart_width, y)
            self.canv.setDash([], 0)
            
            # 添加刻度标签
            self.canv.setFont("Helvetica", 8)
            self.canv.setFillColor(COLOR_THEME['text'])
            self.canv.drawRightString(margin_left - 8, y - 3, f"{i * 20}%")
        
        # 绘制X轴
        self.canv.setStrokeColor(COLOR_THEME['text'])
        self.canv.line(margin_left, margin_bottom, margin_left + chart_width, margin_bottom)
        
        # 绘制柱状图和标签
        for i, (score, domain) in enumerate(zip(self.scores, self.domains)):
            # 计算柱子位置
            x = margin_left + spacing + i * (bar_width + spacing)
            y = margin_bottom
            height = chart_height * score
            
            # 使用ModelCompare.vue中的评分颜色
            if score >= 0.9:
                bar_color = colors.HexColor('#67C23A')  # 优秀 - 绿色
            elif score >= 0.8:
                bar_color = colors.HexColor('#409EFF')  # 良好 - 蓝色
            elif score >= 0.6:
                bar_color = colors.HexColor('#E6A23C')  # 及格 - 黄色
            else:
                bar_color = colors.HexColor('#F56C6C')  # 不及格 - 红色
                
            self.canv.setFillColor(bar_color)
            
            # 绘制柱子
            self.canv.rect(x, y, bar_width, height, fill=1, stroke=0)
            
            # 添加分数标签
            self.canv.setFont("Helvetica", 9)
            self.canv.setFillColor(COLOR_THEME['text'])
            score_label = f"{score*100:.1f}%"
            self.canv.drawCentredString(x + bar_width/2, y + height + 5, score_label)
            
            # 添加领域标签，旋转以节省空间
            font_name = self.chinese_font if self.chinese_font else "Helvetica"
            self.canv.setFont(font_name, 8)
            
            # 绘制垂直文本
            domain_label = domain
            if len(domain_label) > 10:
                domain_label = domain_label[:10] + "..."
                
            # 绘制域名标签，旋转45度
            self.canv.saveState()
            self.canv.translate(x + bar_width/2, y - 8)
            self.canv.rotate(-45)
            self.canv.drawCentredString(0, 0, domain_label)
            self.canv.restoreState()

# 自定义Flowable: 雷达图
class RadarChart(Flowable):
    """创建雷达图显示各领域评分"""
    
    def __init__(self, width, height, values, labels, chinese_font=None, title=None):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.values = values  # 0-1之间的分数列表
        self.labels = labels  # 标签列表
        self.chinese_font = chinese_font
        self.title = title
    
    def draw(self):
        # 确定雷达图位置和大小
        cx = self.width / 2  # 中心X坐标
        cy = self.height / 2  # 中心Y坐标
        radius = min(cx, cy) - 30  # 半径
        
        # 绘制标题
        if self.title:
            font_name = self.chinese_font if self.chinese_font else "Helvetica-Bold"
            self.canv.setFont(font_name, 14)
            self.canv.setFillColor(COLOR_THEME['primary'])
            self.canv.drawCentredString(cx, self.height - 15, self.title)
        
        # 需要确保有数据
        if not self.values or not self.labels:
            self.canv.setFont("Helvetica", 12)
            self.canv.setFillColor(COLOR_THEME['text'])
            self.canv.drawCentredString(cx, cy, "没有可用数据")
            return
        
        # 计算边数
        sides = len(self.values)
        if sides < 3:
            # 至少需要3边才能绘制一个多边形
            self.canv.setFont("Helvetica", 12)
            self.canv.setFillColor(COLOR_THEME['text'])
            self.canv.drawCentredString(cx, cy, "至少需要3个数据点")
            return
        
        # 计算每条边的角度
        angle_step = 2 * math.pi / sides
        
        # 绘制背景网格
        for i in range(5):  # 绘制5个同心圆
            level = (i + 1) / 5
            self.canv.setStrokeColor(COLOR_THEME['radar_grid'])
            self.canv.setLineWidth(0.5)
            
            # 绘制同心多边形
            points = []
            for j in range(sides):
                angle = j * angle_step - math.pi / 2  # 从上方开始
                r = radius * level
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                points.append((x, y))
            
            # 绘制多边形
            self.canv.setStrokeColor(COLOR_THEME['radar_grid'])
            self.canv.setFillColor(colors.white)
            
            path = self.canv.beginPath()
            path.moveTo(points[0][0], points[0][1])
            for x, y in points[1:]:
                path.lineTo(x, y)
            path.close()
            self.canv.drawPath(path, stroke=1, fill=0)
            
            # 标记比例
            if i == 4:  # 只在最外层标记
                self.canv.setFont("Helvetica", 8)
                self.canv.setFillColor(COLOR_THEME['text_light'])
                self.canv.drawCentredString(cx, cy - radius - 10, "100%")
            if i == 1:  # 40%
                self.canv.drawCentredString(cx, cy - (radius * 0.4) - 10, "40%")
            if i == 3:  # 80%
                self.canv.drawCentredString(cx, cy - (radius * 0.8) - 10, "80%")
        
        # 绘制轴线
        for i in range(sides):
            angle = i * angle_step - math.pi / 2  # 从上方开始
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            self.canv.setStrokeColor(COLOR_THEME['radar_grid'])
            self.canv.line(cx, cy, x, y)
            
            # 添加标签
            if i < len(self.labels):
                label = self.labels[i]
                font_name = self.chinese_font if self.chinese_font else "Helvetica"
                self.canv.setFont(font_name, 9)
                self.canv.setFillColor(COLOR_THEME['text'])
                
                # 根据角度调整标签位置
                label_x = cx + (radius + 15) * math.cos(angle)
                label_y = cy + (radius + 15) * math.sin(angle)
                
                # 根据象限调整对齐方式
                if -0.25 * math.pi <= angle <= 0.25 * math.pi:  # 右
                    self.canv.drawString(label_x, label_y - 5, label)
                elif 0.25 * math.pi < angle <= 0.75 * math.pi:  # 下
                    self.canv.drawCentredString(label_x, label_y, label)
                elif 0.75 * math.pi < angle <= 1.25 * math.pi:  # 左
                    self.canv.drawRightString(label_x, label_y - 5, label)
                else:  # 上
                    self.canv.drawCentredString(label_x, label_y - 10, label)
        
        # 绘制数据多边形
        data_points = []
        for i, value in enumerate(self.values):
            if i >= sides:
                break
            
            angle = i * angle_step - math.pi / 2  # 从上方开始
            r = radius * value  # 根据值缩放半径
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            data_points.append((x, y))
        
        # 绘制填充多边形
        self.canv.setStrokeColor(COLOR_THEME['radar_line'])
        # 使用半透明颜色
        fill_color = colors.Color(
            COLOR_THEME['radar_fill'].red,
            COLOR_THEME['radar_fill'].green,
            COLOR_THEME['radar_fill'].blue,
            alpha=0.5
        )
        self.canv.setFillColor(fill_color)
        
        path = self.canv.beginPath()
        path.moveTo(data_points[0][0], data_points[0][1])
        for x, y in data_points[1:]:
            path.lineTo(x, y)
        path.close()
        self.canv.drawPath(path, stroke=1, fill=1)
        
        # 在每个数据点添加点
        for x, y in data_points:
            self.canv.setFillColor(COLOR_THEME['radar_line'])
            self.canv.circle(x, y, 3, fill=1, stroke=0)

# 自定义Flowable: 趋势图
class TrendChart(Flowable):
    """创建趋势图显示评分变化"""
    
    def __init__(self, width, height, scores, dates=None, chinese_font=None, title=None):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.scores = scores  # 分数列表
        
        # 如果没有提供日期，则使用索引
        if dates is None:
            self.dates = list(range(1, len(scores) + 1))
        else:
            self.dates = dates
            
        self.chinese_font = chinese_font
        self.title = title
    
    def draw(self):
        # 确保有数据
        if not self.scores:
            return
        
        # 设置图表区域
        margin = 40
        chart_width = self.width - 2 * margin
        chart_height = self.height - 2 * margin
        
        # 绘制标题
        if self.title:
            font_name = self.chinese_font if self.chinese_font else "Helvetica-Bold"
            self.canv.setFont(font_name, 14)
            self.canv.setFillColor(COLOR_THEME['primary'])
            self.canv.drawCentredString(self.width / 2, self.height - 15, self.title)
        
        # 绘制坐标轴
        self.canv.setStrokeColor(COLOR_THEME['text'])
        self.canv.setLineWidth(1)
        
        # X轴
        self.canv.line(margin, margin, margin + chart_width, margin)
        # Y轴
        self.canv.line(margin, margin, margin, margin + chart_height)
        
        # 计算刻度
        max_score = max(self.scores)
        min_score = min(self.scores)
        
        # 确保Y轴范围合适
        if max_score == min_score:
            max_score += 0.1
            min_score = max(0, min_score - 0.1)
        
        # 确保范围在0-1之间
        min_score = max(0, min_score - 0.1)
        max_score = min(1, max_score + 0.1)
        
        # Y轴刻度
        for i in range(6):  # 0%, 20%, 40%, 60%, 80%, 100%
            y_value = i / 5
            y_pos = margin + chart_height * (1 - y_value / max_score)
            
            # 绘制刻度线
            self.canv.setStrokeColor(COLOR_THEME['text_light'])
            self.canv.line(margin - 5, y_pos, margin, y_pos)
            
            # 绘制网格线
            self.canv.setStrokeColor(COLOR_THEME['radar_grid'])
            self.canv.setDash([1, 2], 0)
            self.canv.line(margin, y_pos, margin + chart_width, y_pos)
            self.canv.setDash([], 0)
            
            # 绘制刻度值
            self.canv.setFont("Helvetica", 8)
            self.canv.setFillColor(COLOR_THEME['text'])
            self.canv.drawRightString(margin - 8, y_pos - 3, f"{int(y_value * 100)}%")
        
        # X轴刻度 - 根据数据点数量动态调整
        point_count = len(self.scores)
        step = max(1, point_count // 5)  # 最多显示5个刻度
        
        for i in range(0, point_count, step):
            x_pos = margin + (i / (point_count - 1)) * chart_width if point_count > 1 else margin + chart_width / 2
            
            # 绘制刻度线
            self.canv.setStrokeColor(COLOR_THEME['text_light'])
            self.canv.line(x_pos, margin, x_pos, margin - 5)
            
            # 绘制网格线
            self.canv.setStrokeColor(COLOR_THEME['radar_grid'])
            self.canv.setDash([1, 2], 0)
            self.canv.line(x_pos, margin, x_pos, margin + chart_height)
            self.canv.setDash([], 0)
            
            # 绘制刻度值
            date_label = str(self.dates[i]) if i < len(self.dates) else ""
            self.canv.setFont("Helvetica", 8)
            self.canv.setFillColor(COLOR_THEME['text'])
            
            # 如果是日期，则截取月日
            if isinstance(date_label, str) and len(date_label) > 5:
                try:
                    # 尝试解析为日期格式
                    date = datetime.datetime.fromisoformat(date_label.replace('Z', '+00:00'))
                    date_label = date.strftime("%m-%d")
                except (ValueError, TypeError):
                    pass
                    
            self.canv.drawCentredString(x_pos, margin - 15, date_label)
        
        # 绘制折线
        if point_count > 1:
            points = []
            
            for i, score in enumerate(self.scores):
                x_pos = margin + (i / (point_count - 1)) * chart_width
                y_pos = margin + chart_height * (1 - score / max_score)
                points.append((x_pos, y_pos))
            
            # 绘制线段
            self.canv.setStrokeColor(COLOR_THEME['secondary'])
            self.canv.setLineWidth(2)
            
            path = self.canv.beginPath()
            path.moveTo(points[0][0], points[0][1])
            for x, y in points[1:]:
                path.lineTo(x, y)
            self.canv.drawPath(path, stroke=1, fill=0)
            
            # 绘制数据点
            for x, y in points:
                self.canv.setFillColor(COLOR_THEME['accent'])
                self.canv.circle(x, y, 3, fill=1, stroke=0)
                
                # 标记分数值
                score_index = points.index((x, y))
                score_value = self.scores[score_index]
                score_text = f"{int(score_value * 100)}%"
                
                self.canv.setFont("Helvetica", 8)
                self.canv.setFillColor(COLOR_THEME['text'])
                self.canv.drawCentredString(x, y - 10, score_text)
        
        # 绘制单个点
        elif point_count == 1:
            score = self.scores[0]
            x_pos = margin + chart_width / 2
            y_pos = margin + chart_height * (1 - score / max_score)
            
            self.canv.setFillColor(COLOR_THEME['accent'])
            self.canv.circle(x_pos, y_pos, 4, fill=1, stroke=0)
            
            # 标记分数值
            score_text = f"{int(score * 100)}%"
            self.canv.setFont("Helvetica", 9)
            self.canv.setFillColor(COLOR_THEME['text'])
            self.canv.drawCentredString(x_pos, y_pos - 12, score_text)

# 修改生成PDF的函数，确保使用中文字体，并支持领域评测报告格式
def generate_report_pdf(report_data, file_name=None, logo_path=None):
    """
    生成PDF报告
    :param report_data: 报告数据（字典）
    :param file_name: 文件名（可选）
    :param logo_path: Logo文件路径（可选）
    :return: 包含PDF数据的BytesIO对象
    """
    try:
        # 打印调试信息
        logger.info(f"开始生成PDF报告: {file_name}")
        logger.info(f"报告数据类型: {type(report_data)}")
        
        if not report_data:
            raise ValueError('报告数据为空')

        # 创建一个内存缓冲区存储PDF
        buffer = io.BytesIO()
        
        # 设置页面大小和边距
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,   
            topMargin=2.5*cm,   
            bottomMargin=2*cm  
        )
        
        # 内容列表
        elements = []
        
        # 获取样式
        styles = getSampleStyleSheet()
        
        # 设置标题
        title_text = file_name or '模型领域评估报告'
        
        # 创建自定义中文样式
        if chinese_font:
            # 创建支持中文的标题样式
            cn_title_style = ParagraphStyle(
                'ChineseTitle',
                parent=styles['Title'],
                fontName=chinese_font,
                fontSize=24,
                alignment=1,  # 居中
                textColor=COLOR_THEME['primary'],
                spaceAfter=12,
                leading=28
            )
            
            # 创建支持中文的正文样式
            cn_normal_style = ParagraphStyle(
                'ChineseNormal',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=10,
                textColor=COLOR_THEME['text'],
                leading=14
            )
            
            # 创建支持中文的标题1样式
            cn_heading1_style = ParagraphStyle(
                'ChineseHeading1',
                parent=styles['Heading1'],
                fontName=chinese_font,
                fontSize=20,
                textColor=COLOR_THEME['primary'],
                spaceBefore=12,
                spaceAfter=12,
                keepWithNext=True,
                leading=24
            )
            
            # 创建支持中文的标题2样式
            cn_heading2_style = ParagraphStyle(
                'ChineseHeading2',
                parent=styles['Heading2'],
                fontName=chinese_font,
                fontSize=16,
                textColor=COLOR_THEME['secondary'],
                spaceBefore=10,
                spaceAfter=10,
                keepWithNext=True,
                leading=20
            )
            
            # 创建支持中文的标题3样式
            cn_heading3_style = ParagraphStyle(
                'ChineseHeading3',
                parent=styles['Heading3'],
                fontName=chinese_font,
                fontSize=14,
                textColor=COLOR_THEME['tertiary'],
                spaceBefore=8,
                spaceAfter=6,
                keepWithNext=True,
                leading=18
            )
            
            # 创建支持中文的强调样式
            cn_emphasis_style = ParagraphStyle(
                'ChineseEmphasis',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=10,
                textColor=COLOR_THEME['accent'],
                leading=14
            )
            
            # 创建支持中文的注释样式
            cn_note_style = ParagraphStyle(
                'ChineseNote',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=9,
                textColor=COLOR_THEME['text_light'],
                alignment=2,  # 右对齐
                leading=12
            )
            
            # 创建支持中文的引用样式
            cn_quote_style = ParagraphStyle(
                'ChineseQuote',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=10,
                textColor=COLOR_THEME['text'],
                leftIndent=20,
                rightIndent=20,
                leading=14,
                spaceBefore=6,
                spaceAfter=6
            )
            
            # 创建支持中文的表格标题样式
            cn_table_title_style = ParagraphStyle(
                'ChineseTableTitle',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=11,
                textColor=COLOR_THEME['primary'],
                alignment=1,  # 居中
                spaceAfter=6,
                leading=14
            )
            
            # 创建大号数字显示样式
            cn_large_number_style = ParagraphStyle(
                'ChineseLargeNumber',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=36,
                alignment=1,  # 居中
                textColor=COLOR_THEME['primary'],
                leading=40
            )
        else:
            # 如果没有中文字体，使用默认样式
            cn_title_style = styles['Title']
            cn_normal_style = styles['Normal']
            cn_heading1_style = styles['Heading1']
            cn_heading2_style = styles['Heading2']
            cn_heading3_style = styles['Heading3']
            cn_emphasis_style = ParagraphStyle('Emphasis', parent=styles['Normal'], textColor=COLOR_THEME['accent'])
            cn_note_style = ParagraphStyle('Note', parent=styles['Normal'], fontSize=8, textColor=COLOR_THEME['text_light'], alignment=2)
            cn_quote_style = ParagraphStyle('Quote', parent=styles['Normal'], leftIndent=20, rightIndent=20)
            cn_table_title_style = ParagraphStyle('TableTitle', parent=styles['Normal'], fontSize=11, textColor=COLOR_THEME['primary'], alignment=1)
            cn_large_number_style = ParagraphStyle('LargeNumber', parent=styles['Normal'], fontSize=36, alignment=1, textColor=COLOR_THEME['primary'])
        
        # 创建页面模板
        page_header_footer = PageHeaderFooter(title_text, logo_path, chinese_font)
        
        # 配置页面模板
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
        template = PageTemplate(id='Later', frames=[frame], onPage=page_header_footer)
        doc.addPageTemplates([template])
        
        # 添加封面
        model_info = report_data.get('model_info', {})
        cover = CoverPage(title_text, logo_path=logo_path, model_info=model_info, chinese_font=chinese_font)
        elements.append(cover)
        elements.append(PageBreak())
        
        # 添加报告概览
        elements.append(Paragraph("1. 报告概览", cn_heading1_style))
        #elements.append(InfoBox("本报告展示了模型在各个领域的评测结果，包括平均得分、评测次数等信息，以及模型在各领域的优势和不足。", doc.width))
        #elements.append(Spacer(1, 0.5*cm))
        
        # 领域评测统计
        domains = report_data.get('domains', [])
        
        if domains:
            overview_text = f"本次评估覆盖了{len(domains)}个领域，共进行了{sum(domain.get('total_evaluations', 0) for domain in domains)}次评测。"
            elements.append(Paragraph(overview_text, cn_normal_style))
            elements.append(Spacer(1, 0.5*cm))
            
            # 计算整体平均分
            all_scores = [domain.get('average_score', 0) for domain in domains]
            overall_avg = sum(all_scores) / len(all_scores) if all_scores else 0
            overall_grade, overall_color = get_score_grade(overall_avg)
            
            # 使用表格和大字号数字替代仪表盘
            elements.append(Paragraph("模型总体评分", cn_table_title_style))
            elements.append(Spacer(1, 0.3*cm))
            
            # 创建大号数字显示总分
            score_percent = f"{overall_avg*100:.2f}%"
            elements.append(Paragraph(score_percent, cn_large_number_style))
            
            # 显示等级
            grade_text = f"评级: {overall_grade} ({get_score_description(overall_avg)})"
            grade_style = ParagraphStyle(
                'GradeStyle', 
                parent=cn_normal_style,
                alignment=1,  # 居中
                textColor=overall_color,
                fontSize=14
            )
            elements.append(Paragraph(grade_text, grade_style))
            elements.append(Spacer(1, 0.5*cm))
            
            # 添加评价文本，不使用InfoBox
            overall_description = get_score_description(overall_avg)
            overall_feedback = f"模型整体评分为{overall_avg*100:.2f}%，评级为【{overall_grade}】：{overall_description}。"
            elements.append(Paragraph(overall_feedback, cn_normal_style))
            elements.append(Spacer(1, 1.0*cm))  # 增加间距，避免重叠
            
            # 添加评分等级说明
            elements.append(Paragraph("评分等级说明", cn_table_title_style))
            elements.append(Spacer(1, 0.3*cm))
            elements.append(ScoreGradeTable(width=doc.width * 0.6, height=100, chinese_font=chinese_font))
            elements.append(Spacer(1, 1.0*cm))  # 增加间距，避免重叠
            
            # *** 不再添加页面分隔符，将模型信息直接放到报告概览后面 ***
            elements.append(Paragraph("2. 模型基本信息", cn_heading1_style))
            elements.append(Spacer(1, 0.5*cm))
            
            if model_info:
                # 构建表格数据
                model_name = model_info.get('name', '')
                last_update = model_info.get('last_update', '')
                
                data = [
                    ['模型名称', model_name],
                    ['最后更新时间', last_update]
                ]
                
                # 可以添加更多模型信息行
                if 'version' in model_info:
                    data.append(['版本', model_info['version']])
                if 'description' in model_info:
                    data.append(['描述', model_info['description']])
                if 'provider' in model_info:
                    data.append(['提供商', model_info['provider']])
                
                # 设置中文字体的表格样式
                table_style = [
                    ('BACKGROUND', (0, 0), (0, -1), COLOR_THEME['table_header']),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, COLOR_THEME['text_light'])
                ]
                
                # 如果有中文字体，添加字体设置
                if chinese_font:
                    table_style.extend([
                        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                        ('FONTSIZE', (0, 0), (-1, -1), 10)
                    ])
                else:
                    table_style.append(('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'))
                
                # 创建表格
                model_table = Table(data, colWidths=[doc.width*0.25, doc.width*0.75])
                model_table.setStyle(TableStyle(table_style))
                elements.append(model_table)
                elements.append(Spacer(1, 1*cm))
            
            # 添加页面分隔符，准备进入领域评测章节
            elements.append(PageBreak())
            
            # 领域评测统计总览
            if domains:
                elements.append(Paragraph("3. 领域评测总览", cn_heading1_style))
                elements.append(Spacer(1, 0.5*cm))
                
                # 构建表格数据
                elements.append(Paragraph("领域评测统计表", cn_heading3_style))
                elements.append(Spacer(1, 0.3*cm))
                
                data = [['领域', '平均得分', '评测次数', '等级']]
                domains_scores = []
                domains_names = []
                
                # 按照得分从高到低排序领域
                sorted_domains = sorted(domains, key=lambda x: x.get('average_score', 0), reverse=True)
                
                for domain in sorted_domains:
                    name = domain.get('name', '')
                    avg_score = domain.get('average_score', 0)
                    total_evals = domain.get('total_evaluations', 0)
                    
                    domains_names.append(name)
                    domains_scores.append(avg_score)
                    
                    # 获取等级和颜色
                    grade, _ = get_score_grade(avg_score)
                    
                    # 格式化平均分数为百分比
                    avg_score_formatted = f"{avg_score * 100:.2f}%" if isinstance(avg_score, (int, float)) else avg_score
                    
                    data.append([
                        name,
                        avg_score_formatted,
                        total_evals,
                        grade
                    ])
                
                # 设置表格样式
                domain_table_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), COLOR_THEME['table_header']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, COLOR_THEME['text_light']),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_THEME['table_alt_row']])
                ]
                
                if chinese_font:
                    domain_table_style.extend([
                        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('FONTSIZE', (0, 1), (-1, -1), 10)
                    ])
                
                domain_table = Table(data, colWidths=[doc.width*0.3, doc.width*0.2, doc.width*0.2, doc.width*0.3])
                domain_table.setStyle(TableStyle(domain_table_style))
                elements.append(domain_table)
                elements.append(Spacer(1, 0.8*cm))
                
                # 添加柱状图：显示各领域得分
                elements.append(Paragraph("领域评分柱状图", cn_heading3_style))
                elements.append(Spacer(1, 0.3*cm))
                
                # 创建柱状图
                bar_chart = DomainBarChart(doc.width * 0.8, 250, domains_scores, domains_names, chinese_font=chinese_font)
                elements.append(bar_chart)
                elements.append(Spacer(1, 0.8*cm))
                
                # 添加雷达图：显示各领域得分
                elements.append(Paragraph("领域评分雷达图", cn_heading3_style))
                elements.append(Spacer(1, 0.3*cm))
                
                # 创建雷达图
                radar = RadarChart(doc.width * 0.6, 250, domains_scores, domains_names, chinese_font=chinese_font)
                elements.append(radar)
                elements.append(Spacer(1, 0.8*cm))
                
                # 添加简短的数据解读
                if len(domains_scores) >= 3:
                    # 找出最高和最低分数的领域
                    max_score_idx = domains_scores.index(max(domains_scores))
                    min_score_idx = domains_scores.index(min(domains_scores))
                    
                    max_domain = domains_names[max_score_idx]
                    min_domain = domains_names[min_score_idx]
                    
                    analysis_text = f"从图表中可以看出，模型在【{max_domain}】领域表现最好（{domains_scores[max_score_idx]*100:.2f}%），而在【{min_domain}】领域表现相对较弱（{domains_scores[min_score_idx]*100:.2f}%）。"
                    elements.append(Paragraph(analysis_text, cn_normal_style))
                    elements.append(Spacer(1, 0.5*cm))
                
                # 添加页面分隔符
                elements.append(PageBreak())
                
                # 添加各领域评测详情
                elements.append(Paragraph("4. 各领域评测详情", cn_heading1_style))
                elements.append(Spacer(1, 0.5*cm))
                
                # 对每个领域添加详细信息 - 连续写，不分页
                for i, domain in enumerate(sorted_domains):
                    domain_name = domain.get('name', f'领域{i+1}')
                    domain_score = domain.get('average_score', 0)
                    domain_evals = domain.get('total_evaluations', 0)
                    domain_grade, domain_color = get_score_grade(domain_score)
                    
                    # 添加领域标题
                    elements.append(Paragraph(f"4.{i+1} {domain_name}", cn_heading2_style))
                    elements.append(Spacer(1, 0.3*cm))
                    
                    # 添加领域基本信息
                    domain_info_text = f"{domain_name}领域评分为{domain_score*100:.2f}%，评级为【{domain_grade}】，共进行了{domain_evals}次评测。"
                    elements.append(Paragraph(domain_info_text, cn_normal_style))
                    
                    # 添加题目回答情况
                    correct_questions = domain.get('correct_count', 0)
                    total_questions = domain.get('total_questions', domain_evals * 3)  # 假设每次评测平均3道题
                    
                    # 如果数据中没有提供正确题数，根据平均分估算
                    if correct_questions == 0 and total_questions > 0:
                        correct_questions = int(domain_score * total_questions)
                    
                    question_info_text = f"共回答{total_questions}道题目，答对{correct_questions}道，正确率{(correct_questions/total_questions)*100:.2f}%。"
                    elements.append(Paragraph(question_info_text, cn_normal_style))
                    elements.append(Spacer(1, 0.5*cm))
                    
                    # 添加趋势图（如果有历史数据）
                    history = domain.get('history', [])
                    if history and len(history) > 1:
                        elements.append(Paragraph(f"{domain_name}评分趋势", cn_heading3_style))
                        elements.append(Spacer(1, 0.3*cm))
                        
                        history_scores = [h.get('score', 0) for h in history]
                        history_dates = [h.get('date', '') for h in history]
                        
                        trend_chart = TrendChart(doc.width * 0.7, 150, history_scores, history_dates, chinese_font=chinese_font)
                        elements.append(trend_chart)
                        elements.append(Spacer(1, 0.5*cm))
                    
                    # 添加关键词和标签
                    keywords = domain.get('keywords', [])
                    if keywords:
                        elements.append(Paragraph("关键词分析", cn_heading3_style))
                        elements.append(Spacer(1, 0.3*cm))
                        
                        keywords_text = ", ".join(keywords)
                        elements.append(Paragraph(f"关键词: {keywords_text}", cn_normal_style))
                        elements.append(Spacer(1, 0.5*cm))
                    
                    # 添加具体评测项
                    evaluations = domain.get('evaluations', [])
                    if evaluations:
                        elements.append(Paragraph("评测项详情", cn_heading3_style))
                        elements.append(Spacer(1, 0.3*cm))
                        
                        eval_data = [['评测项', '得分', '权重', '加权得分']]
                        for eval_item in evaluations:
                            item_name = eval_item.get('name', '')
                            item_score = eval_item.get('score', 0)
                            item_weight = eval_item.get('weight', 1)
                            weighted_score = item_score * item_weight
                            
                            # 格式化分数
                            score_formatted = f"{item_score*100:.2f}%"
                            weight_formatted = f"{item_weight:.2f}"
                            weighted_formatted = f"{weighted_score*100:.2f}%"
                            
                            eval_data.append([
                                item_name,
                                score_formatted,
                                weight_formatted,
                                weighted_formatted
                            ])
                        
                        # 设置表格样式
                        eval_table_style = [
                            ('BACKGROUND', (0, 0), (-1, 0), COLOR_THEME['table_header']),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('GRID', (0, 0), (-1, -1), 1, COLOR_THEME['text_light']),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_THEME['table_alt_row']])
                        ]
                        
                        if chinese_font:
                            eval_table_style.extend([
                                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                                ('FONTSIZE', (0, 0), (-1, 0), 10),
                                ('FONTSIZE', (0, 1), (-1, -1), 9)
                            ])
                        
                        eval_table = Table(eval_data, colWidths=[doc.width*0.4, doc.width*0.2, doc.width*0.2, doc.width*0.2])
                        eval_table.setStyle(TableStyle(eval_table_style))
                        elements.append(eval_table)
                        elements.append(Spacer(1, 0.5*cm))
                    
                    # 添加改进建议
                    suggestions = domain.get('suggestions', [])
                    if suggestions:
                        elements.append(Paragraph("改进建议", cn_heading3_style))
                        elements.append(Spacer(1, 0.3*cm))
                        
                        for j, suggestion in enumerate(suggestions):
                            elements.append(Paragraph(f"{j+1}. {suggestion}", cn_normal_style))
                            elements.append(Spacer(1, 0.2*cm))
                    
                    # 添加分隔符（除了最后一个领域）- 使用分隔线而不是分页
                    if i < len(sorted_domains) - 1:
                        elements.append(Spacer(1, 0.5*cm))
                        elements.append(HRFlowable(width="100%", color=COLOR_THEME['text_light'], thickness=1))
                        elements.append(Spacer(1, 0.5*cm))
                
                # 添加结论与建议章节
                elements.append(PageBreak())
                elements.append(Paragraph("5. 结论与建议", cn_heading1_style))
                elements.append(Spacer(1, 0.5*cm))
                
                # 准备强项和弱项领域的详细信息
                # 获取前3名和后3名的领域
                top_3_domains = sorted_domains[:min(3, len(sorted_domains))]
                bottom_3_domains = sorted_domains[-min(3, len(sorted_domains)):]

                # 筛选出表现较佳的领域（分数大于60%且在前3名）
                strong_domains = [d for d in top_3_domains if d.get('average_score', 0) >= 0.6]
                
                # 筛选出表现较弱的领域（分数小于60%且在后3名）
                weak_domains = [d for d in bottom_3_domains if d.get('average_score', 0) < 0.6]

                # 生成领域文本，如果没有符合条件的领域则提供相应说明
                if strong_domains:
                    strong_domains_text = ", ".join([f"{d.get('name', '')}({d.get('average_score', 0)*100:.2f}%)" for d in strong_domains])
                else:
                    strong_domains_text = "暂无表现突出的领域"

                if weak_domains:
                    weak_domains_text = ", ".join([f"{d.get('name', '')}({d.get('average_score', 0)*100:.2f}%)" for d in weak_domains])
                else:
                    weak_domains_text = "暂无特别薄弱的领域"

                # 更详细的总结
                conclusion = report_data.get('conclusion', f"""
                根据评测结果，该模型的整体表现为{overall_avg*100:.2f}%，评级为【{overall_grade}】。

                {f"模型表现较佳的领域是：{strong_domains_text}" if strong_domains else "模型目前没有表现特别突出的领域"}，{"这表明模型在这些领域有较好的知识基础和推理能力。" if strong_domains else "需要继续提升各领域的表现。"}

                {f"模型表现较弱的领域是：{weak_domains_text}" if weak_domains else "模型各领域基础表现尚可"}，{"这些领域需要重点改进。" if weak_domains else "但仍有提升空间。"}

                各领域评分差异明显，表明模型在不同知识领域的能力发展不平衡。
                """)
                
                elements.append(Paragraph("总体结论", cn_heading3_style))
                elements.append(Spacer(1, 0.3*cm))
                
                # 分段显示结论
                conclusion_paragraphs = [p.strip() for p in conclusion.split("\n") if p.strip()]
                for paragraph in conclusion_paragraphs:
                    elements.append(Paragraph(paragraph, cn_normal_style))
                    elements.append(Spacer(1, 0.3*cm))
                
                # 建议
                default_suggestions = [
                    f"针对{weak_domains[0].get('name', '') if weak_domains else '低分领域'}进行专项能力训练，补充相关领域的训练数据。",
                    "平衡各领域的训练数据比例，减少知识偏差。",
                    "增加评测频次，建立持续改进机制。",
                    f"考虑针对{weak_domains_text}领域进行专家知识引入或微调训练。",
                    "持续扩充训练数据的多样性和代表性。"
                ]
                
                suggestions = report_data.get('suggestions', default_suggestions)
                
                elements.append(Paragraph("改进建议", cn_heading3_style))
                elements.append(Spacer(1, 0.3*cm))
                
                for i, suggestion in enumerate(suggestions):
                    elements.append(Paragraph(f"{i+1}. {suggestion}", cn_normal_style))
                    elements.append(Spacer(1, 0.2*cm))
            
        # 构建PDF文档 - 使用标准build方法（因为不再使用TOC）
        doc.build(elements)  # 改回标准build因为没有目录
        
        logger.info("PDF生成成功")
        
        # 将指针移动到缓冲区开始
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        logger.error(f"生成PDF时发生错误: {str(e)}", exc_info=True)
        # 重新创建一个简单的PDF，显示错误信息
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []
            
            elements.append(Paragraph("PDF生成错误", styles['Title']))
            elements.append(Spacer(1, 1*cm))
            elements.append(Paragraph(f"生成PDF时发生错误: {str(e)}", styles['Normal']))
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph("详细错误信息:", styles['Normal']))
            elements.append(Spacer(1, 0.5*cm))
            
            # 记录详细的错误堆栈
            import traceback
            error_stack = traceback.format_exc()
            elements.append(Paragraph(error_stack.replace('\n', '<br/>'), styles['Code']))
            
            doc.build(elements)
            buffer.seek(0)
            return buffer
            
        except Exception as e2:
            logger.error(f"创建错误PDF时也失败了: {str(e2)}")
            # 如果连错误PDF都无法生成，返回一个空的PDF
            buffer = io.BytesIO()
            buffer.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>endobj xref 0 4 0000000000 65535 f 0000000010 00000 n 0000000053 00000 n 0000000102 00000 n trailer<</Size 4/Root 1 0 R>>startxref 178 %%EOF")
            buffer.seek(0)
            return buffer
