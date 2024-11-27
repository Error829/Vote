from pdf2image import convert_from_path
import os
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def convert_pdf_to_images(pdf_path):
    """将PDF文件转换为图片"""
    try:
        logger.info(f"开始转换PDF: {pdf_path}")
        
        # 获取项目根目录
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        # 检查文件是否存在
        if not os.path.exists(pdf_path):
            logger.error(f"PDF文件不存在: {pdf_path}")
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        # 检查文件权限
        if not os.access(pdf_path, os.R_OK):
            logger.error(f"无法读取PDF文件: {pdf_path}")
            raise PermissionError(f"无法读取PDF文件: {pdf_path}")

        # 转换PDF
        images = convert_from_path(
            pdf_path,
            dpi=200,
            fmt='jpeg',
            thread_count=2,
            size=None
        )
        
        logger.info(f"PDF转换成功，共 {len(images)} 页")
        
        image_paths = []
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        # 使用正确的路径创建图片目录
        image_folder = os.path.join(BASE_DIR, 'static', 'uploads', 'images', pdf_name)
        os.makedirs(image_folder, exist_ok=True)
        logger.info(f"创建图片目录: {image_folder}")
        
        # 保存图片
        for i, image in enumerate(images):
            try:
                image_filename = f'page_{i+1}.jpg'
                image_path = os.path.join(image_folder, image_filename)
                
                # 保存图片
                image.save(image_path, 'JPEG', quality=95)
                logger.info(f"保存图片: {image_path}")
                
                # 存储相对路径（用于URL）
                relative_path = os.path.join('uploads', 'images', pdf_name, image_filename)
                relative_path = relative_path.replace('\\', '/')  # 确保URL使用正斜杠
                image_paths.append(relative_path)
                
            except Exception as e:
                logger.error(f"保存图片失败: {str(e)}")
                raise
        
        logger.info("PDF转换完成")
        return image_paths
        
    except Exception as e:
        logger.error(f"PDF转换失败: {str(e)}")
        raise Exception(f"PDF转换失败: {str(e)}") 