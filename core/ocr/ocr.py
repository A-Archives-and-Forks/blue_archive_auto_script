import time
import cv2
from cnocr import CnOcr


class Baas_ocr:
    def __init__(self, logger, ocr_needed=None):
        self.logger = logger
        self.ocrEN = None
        self.ocrCN = None
        self.ocrJP = None
        self.ocrNUM = None
        self.initialized = {
            'CN': False,
            'Global': False,
            'NUM': False,
            'JP': False
        }
        self.init(ocr_needed)

    def init(self, ocr_needed):
        try:
            self.logger.info("ocr needed: " + str(ocr_needed))
            if 'NUM' in ocr_needed:
                self.init_NUMocr()
            if 'CN' in ocr_needed:
                self.init_CNocr()
            if 'Global' in ocr_needed:
                self.init_ENocr()
            if 'JP' in ocr_needed:
                self.init_JPocr()
        except Exception as e:
            self.logger.error("OCR init error: " + str(e))
            raise e

    def init_ENocr(self):
        if self.ocrEN is None:
            self.ocrEN = CnOcr(det_model_name="en_PP-OCRv3_det",
                               det_model_fp='src/ocr_models/en_PP-OCRv3_det_infer.onnx',
                               rec_model_name='en_number_mobile_v2.0',
                               rec_model_fp='src/ocr_models/en_number_mobile_v2.0_rec_infer.onnx', )
            img_EN = cv2.imread('src/test_ocr/EN.png')
            self.logger.info("Test ocrEN : " + self.ocrEN.ocr_for_single_line(img_EN)['text'])
        return True

    def init_CNocr(self):
        if self.ocrCN is None:
            self.ocrCN = CnOcr(det_model_name='ch_PP-OCRv3_det',
                               det_model_fp='src/ocr_models/ch_PP-OCRv3_det_infer.onnx',
                               rec_model_name='densenet_lite_114-fc',
                               rec_model_fp='src/ocr_models/cn_densenet_lite_136.onnx')
            img_CN = cv2.imread('src/test_ocr/CN.png')
            self.logger.info("Test ocrCN : " + self.ocrCN.ocr_for_single_line(img_CN)['text'])
        return True

    def init_NUMocr(self):
        if self.ocrNUM is None:
            self.ocrNUM = CnOcr(det_model_name='en_PP-OCRv3_det',
                                det_model_fp='src/ocr_models/en_PP-OCRv3_det_infer.onnx',
                                rec_model_name='number-densenet_lite_136-fc',
                                rec_model_fp='src/ocr_models/number-densenet_lite_136.onnx')

            img_NUM = cv2.imread('src/test_ocr/NUM.png')
            self.logger.info("Test ocrNUM : " + self.ocrNUM.ocr_for_single_line(img_NUM)['text'])
        return True

    def init_JPocr(self):
        if self.ocrJP is None:
            from core.ocr.jp_ocr import PPOCR_JP
            self.ocrJP = PPOCR_JP()
            img_JP = cv2.imread('src/test_ocr/JP.png')
            self.logger.info("Test ocrJP : " + self.ocrJP.ocr_for_single_line(img_JP)['text'])

    def recognize_number(self, img, area, category=int, ratio=1.0):
        img = self.get_area_img(img, area, ratio)
        res = self.ocrNUM.ocr_for_single_line(img)['text']
        res = res.replace('<unused3>', '')
        res = res.replace('<unused2>', '')
        temp = ''
        for i in range(0, len(res)):
            if res[i].isdigit():
                temp += res[i]
            elif res[i] == '.' and category == float:
                temp += res[i]

        if temp == '':
            return "UNKNOWN"
        # 不提倡返回值类型不统一
        # 涉及的引用太多了 不敢改
        return category(temp)

    def recognize_int(self, img, area, ratio=1.0) -> int:
        img = self.get_area_img(img, area, ratio)
        res = self.ocrNUM.ocr_for_single_line(img)['text']
        res = res.replace('<unused3>', '').replace('<unused2>', '')

        result = 0
        for i in range(0, len(res)):
            if res[i].isdigit():
                result = result * 10 + int(res[i])
        return result

    def get_region_pure_english(self, img, region, ratio=1.0):
        img = self.get_area_img(img, region, ratio)
        res = self.ocrEN.ocr_for_single_line(img)['text']
        res = res.replace('<unused3>', '')
        res = res.replace('<unused2>', '')
        temp = ''
        for i in range(0, len(res)):
            if self.is_english(res[i]):
                temp += res[i]
        return temp

    def get_region_pure_chinese(self, img, region, ratio=1.0):
        img = self.get_area_img(img, region, ratio)
        res = self.ocrCN.ocr_for_single_line(img)['text']
        res = res.replace('<unused3>', '')
        res = res.replace('<unused2>', '')
        temp = ''
        for i in range(0, len(res)):
            if self.is_chinese_char(res[i]):
                temp += res[i]
        return temp

    def is_upper_english(self, char):
        if 'A' <= char <= 'Z':
            return True
        return False

    def is_lower_english(self, char):
        if 'a' <= char <= 'z':
            return True
        return False

    def is_english(self, char):
        return self.is_upper_english(char) or self.is_lower_english(char)

    def is_chinese_char(self, char):
        return 0x4e00 <= ord(char) <= 0x9fff

    def get_region_res(self, img, region, model='CN', ratio=1.0):
        img = self.get_area_img(img, region, ratio)
        res = ""
        if model == 'CN':
            res = self.ocrCN.ocr_for_single_line(img)['text']
        elif model == 'Global':
            res = self.ocrEN.ocr_for_single_line(img)['text']
        elif model == 'NUM':
            res = self.ocrNUM.ocr_for_single_line(img)['text']
        elif model == 'JP':
            res = self.ocrJP.ocr_for_single_line(img)['text']
        res = res.replace('<unused3>', '')
        res = res.replace('<unused2>', '')
        return res

    def get_region_raw_res(self, img, region, model='CN', ratio=1.0):
        img = self.get_area_img(img, region, ratio)
        res = ""
        if model == 'CN':
            res = self.ocrCN.ocr(img)
        elif model == 'Global':
            res = self.ocrEN.ocr(img)
        elif model == 'NUM':
            res = self.ocrNUM.ocr(img)
        elif model == 'JP':
            res = self.ocrJP.ocr(img)
        for i in range(0, len(res)):
            res[i]['text'] = res[i]['text'].replace('<unused3>', '')
            res[i]['text'] = res[i]['text'].replace('<unused2>', '')
        return res

    def get_area_img(self, img, area, ratio=1.0):
        img = img[int(area[1] * ratio):int(area[3] * ratio), int(area[0] * ratio):int(area[2] * ratio)]
        return img
