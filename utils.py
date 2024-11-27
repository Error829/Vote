from pdf2image import convert_from_path
import os

def convert_pdf_to_images(pdf_path):
    """将PDF文件转换为图片"""
    images = convert_from_path(pdf_path)
    image_paths = []
    
    base_path = os.path.join('static', 'uploads', 'images')
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    for i, image in enumerate(images):
        image_path = os.path.join(base_path, f'{pdf_name}_page_{i+1}.jpg')
        image.save(image_path, 'JPEG')
        image_paths.append(image_path.replace('static/', ''))
    
    return image_paths 