# 确保中文字体文件存在并正确注册
import os
import io
import re  # 添加正则表达式模块导入
import datetime
import logging
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# 设置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.info(f"找到字体文件: {path}")
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
                logger.info(f"成功注册中文字体: {font_name} ({font_path})")
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

# 添加页码的函数
def add_page_number(canvas, doc):
    """
    为每一页添加页码
    """
    page_num = canvas.getPageNumber()
    text = f"页码 {page_num}"
    
    # 如果有注册的中文字体，使用中文字体
    if chinese_font:
        canvas.setFont(chinese_font, 9)
    else:
        canvas.setFont("Helvetica", 9)
        
    canvas.drawRightString(
        doc.pagesize[0] - 2*cm, 
        1*cm, 
        text
    )

# 在生成PDF之前调用这个函数
chinese_font = register_chinese_font()

# 修改生成PDF的函数，确保使用中文字体，并支持领域评测报告格式
def generate_report_pdf(report_data, file_name=None):
    """
    生成PDF报告
    :param report_data: 报告数据（字典）
    :param file_name: 文件名（可选）
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
            topMargin=2*cm, 
            bottomMargin=2*cm
        )
        
        # 内容列表
        elements = []
        
        # 获取样式
        styles = getSampleStyleSheet()
        
        # 创建自定义中文样式
        if chinese_font:
            # 创建支持中文的标题样式
            cn_title_style = ParagraphStyle(
                'ChineseTitle',
                parent=styles['Title'],
                fontName=chinese_font,
                fontSize=20,
                alignment=1  # 居中
            )
            
            # 创建支持中文的正文样式
            cn_normal_style = ParagraphStyle(
                'ChineseNormal',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=10
            )
            
            # 创建支持中文的标题2样式
            cn_heading2_style = ParagraphStyle(
                'ChineseHeading2',
                parent=styles['Heading2'],
                fontName=chinese_font,
                fontSize=14
            )
        else:
            # 如果没有中文字体，使用默认样式
            cn_title_style = styles['Title']
            cn_normal_style = styles['Normal']
            cn_heading2_style = styles['Heading2']
        
        # 创建标题段落
        title_text = file_name or '模型领域评估报告'
        title = Paragraph(title_text, cn_title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        # 添加生成时间
        date_text = f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        date = Paragraph(date_text, cn_normal_style)
        elements.append(date)
        elements.append(Spacer(1, 1*cm))
        
        # 模型信息
        model_info = None
        if 'model_info' in report_data:
            model_info = report_data['model_info']
            
        if model_info:
            elements.append(Paragraph('模型信息', cn_heading2_style))
            elements.append(Spacer(1, 0.3*cm))
            
            # 构建表格数据
            model_name = model_info.get('name', '')
            last_update = model_info.get('last_update', '')
            
            data = [['模型名称', '最后更新时间']]
            data.append([model_name, last_update])
            
            # 设置中文字体的表格样式
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ])
            
            # 如果有中文字体，添加字体设置
            if chinese_font:
                table_style.add('FONTNAME', (0, 0), (-1, -1), chinese_font)
            else:
                table_style.add('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
            
            model_table = Table(data, colWidths=[doc.width/2.0]*2)
            model_table.setStyle(table_style)
            elements.append(model_table)
            elements.append(Spacer(1, 0.5*cm))
        
        # 领域评测统计
        domains = report_data.get('domains', [])
            
        if domains:
            elements.append(Paragraph('领域评测统计', cn_heading2_style))
            elements.append(Spacer(1, 0.3*cm))
            
            # 构建表格数据
            data = [['领域', '平均得分', '评测次数']]
            
            for domain in domains:
                name = domain.get('name', '')
                avg_score = domain.get('average_score', 0)
                total_evals = domain.get('total_evaluations', 0)
                
                # 格式化平均分数为百分比
                avg_score_formatted = f"{avg_score * 100:.2f}%" if isinstance(avg_score, (int, float)) else avg_score
                
                data.append([
                    name,
                    avg_score_formatted,
                    total_evals
                ])
            
            # 设置中文字体的表格样式
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ])
            
            # 如果有中文字体，添加字体设置
            if chinese_font:
                table_style.add('FONTNAME', (0, 0), (-1, -1), chinese_font)
            else:
                table_style.add('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
            
            domain_table = Table(data, colWidths=[doc.width/3.0]*3)
            domain_table.setStyle(table_style)
            elements.append(domain_table)
            elements.append(Spacer(1, 0.5*cm))
            
            # 添加每个领域的详细测评记录
            for domain in domains:
                domain_name = domain.get('name', '')
                scores = domain.get('scores', [])
                
                if scores:
                    elements.append(Paragraph(f"{domain_name}领域评测历史", cn_heading2_style))
                    elements.append(Spacer(1, 0.3*cm))
                    
                    # 构建表格数据
                    data = [['评测时间', '问题数', '正确回答数', '得分']]
                    
                    for score_record in scores:
                        timestamp = score_record.get('timestamp', '')
                        total_questions = score_record.get('total_questions', 0)
                        correct_answers = score_record.get('correct_answers', 0)
                        score = score_record.get('score', 0)
                        
                        # 格式化时间戳
                        if timestamp:
                            timestamp_match = re.match(r'^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$', timestamp)
                            if timestamp_match:
                                y, m, d, h, min, s = timestamp_match.groups()
                                formatted_time = f"{y}-{m}-{d} {h}:{min}:{s}"
                            else:
                                formatted_time = timestamp
                        else:
                            formatted_time = "未知时间"
                        
                        # 格式化得分为百分比
                        score_formatted = f"{score * 100:.2f}%" if isinstance(score, (int, float)) else score
                        
                        data.append([
                            formatted_time,
                            total_questions,
                            correct_answers,
                            score_formatted
                        ])
                    
                    # 设置中文字体的表格样式
                    table_style = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ])
                    
                    # 如果有中文字体，添加字体设置
                    if chinese_font:
                        table_style.add('FONTNAME', (0, 0), (-1, -1), chinese_font)
                    else:
                        table_style.add('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
                    
                    score_table = Table(data, colWidths=[doc.width/4.0]*4)
                    score_table.setStyle(table_style)
                    elements.append(score_table)
                    elements.append(Spacer(1, 0.5*cm))
        
        # 构建PDF文档
        doc.build(
            elements, 
            onFirstPage=add_page_number, 
            onLaterPages=add_page_number
        )
        
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
            
            doc.build(elements)
            buffer.seek(0)
            return buffer
        except:
            # 如果连错误PDF都无法生成，返回一个空的PDF
            buffer = io.BytesIO()
            buffer.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>endobj xref 0 4 0000000000 65535 f 0000000010 00000 n 0000000053 00000 n 0000000102 00000 n trailer<</Size 4/Root 1 0 R>>startxref 178 %%EOF")
            buffer.seek(0)
            return buffer