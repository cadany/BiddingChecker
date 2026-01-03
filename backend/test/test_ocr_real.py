import os
import sys
import cv2
import numpy as np
from PIL import Image
import io
import paddleocr

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_ocr_with_real_image():
    from service.ocr_service import OCRService
    # image_path = "/Users/cadany/Desktop/code/labs/BiddingChecker/files/output/imgs/img_in_image_box_100_28_1144_720.jpg"
    image_path = "/Users/cadany/Desktop/code/labs/BiddingChecker/files/imgs/temp_img_20_1.png"
    image = Image.open(image_path)
    # image = image.crop((100, 28, 1144, 720)) # 裁剪图像，避免OCR识别到图片边框
    
    # 测试OCR服务
    ocr_service = OCRService()
    text = ocr_service.perform_ocr(image)
    print(text)

    # 测试PaddleOCR
    # ocr = paddleocr.PaddleOCR(lang='ch',
    #         use_doc_orientation_classify=True, # 通过 use_doc_orientation_classify 参数指定不使用文档方向分类模型
    #         use_doc_unwarping=False, # 通过 use_doc_unwarping 参数指定不使用文本图像矫正模型
    #         use_textline_orientation=True # 通过 use_textline_orientation 参数指定不使用文本行方向分类模型    
    #     ) 
    # img_array = np.array(image)
    # result = ocr.predict(img_array)
    # texts = result[0]['rec_texts']
    # print(texts)

if __name__ == "__main__":
    test_ocr_with_real_image()
