from pdf2image import convert_from_path
import os

def convert_pdf_to_images(pdf_path):
    """将PDF文件转换为图片"""
    try:
        # 在 Ubuntu 中指定 poppler_path 不是必需的，但需要确保安装了 poppler-utils
        images = convert_from_path(
            pdf_path,
            dpi=200,
            fmt='jpeg',
            thread_count=2,
            size=None
        )
        
        image_paths = []
        
        # 获取PDF文件名（不含扩展名）作为图片文件夹名
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        
        # 创建以PDF名称命名的子文件夹
        image_folder = os.path.join('static', 'uploads', 'images', pdf_name)
        os.makedirs(image_folder, exist_ok=True)
        
        for i, image in enumerate(images):
            # 构建图片保存路径
            image_filename = f'page_{i+1}.jpg'
            image_path = os.path.join(image_folder, image_filename)
            
            # 保存图片
            image.save(image_path, 'JPEG', quality=95)
            
            # 存储相对路径（用于模板中显示）
            relative_path = os.path.join('uploads', 'images', pdf_name, image_filename)
            image_paths.append(relative_path)
            
        return image_paths
        
    except Exception as e:
        print(f"PDF转换错误: {e}")
        raise Exception(f"PDF转换失败: {str(e)}") 