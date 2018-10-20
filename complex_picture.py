import os
import re
import sys
import math
from PIL import Image, ImageOps
from colorsys import rgb_to_hsv
from concurrent.futures import ProcessPoolExecutor

from CONFIG import *
from spider import threading_main


def get_avg_hsv(img):
    """获取一张图片的平均hsv值"""
    # 获取图片的宽高
    width, height = img.size
    pixels = img.load()

    h, s, v = 0, 0, 0
    count = 0
    for x in range(width):
        for y in range(height):
            # 获取rgb值，返回的是一个元组（r, g, b）
            pixel = pixels[x, y]
            # 将rgb转hsv值
            hsv = rgb_to_hsv(*[i/255 for i in pixel])
            h += hsv[0]
            s += hsv[1]
            v += hsv[2]
            count += 1
    if count > 0:
        # 计算hsv的均值
        hAvg = round(h / count, 3)
        sAvg = round(s / count, 3)
        vAvg = round(v / count, 3)
        return hAvg, sAvg, vAvg
    else:
        raise IOError("读取图片数据失败")


def resize_pic(imgName, imgWidth):
    """重定义图片的大小"""
    # 打开图片
    img = Image.open(imgName)
    # 裁剪图片
    # ANTIALIAS 平滑滤波: 对所有可以影响输出像素的输入像素进行高质量的重采样滤波，以计算输出像素值。
    img = ImageOps.fit(img, (imgWidth, imgWidth), Image.ANTIALIAS)
    return img


def get_image_paths():
    """获取所有图片路径"""
    result = os.listdir(IMG_DIR)
    print("一共有[{}]张图片参与此次成像".format(len(result)))
    paths = ["{imgdir}/{filename}".format(imgdir=IMG_DIR, filename=filename) for filename in result]
    return paths


def convert_image(path):
    """转换图片"""
    img = resize_pic(path, SLICE_WIDTH)
    # 获取平均颜色值
    color = get_avg_hsv(img)  # 这一部分返回的是元组
    try:
        # 按规定格式保存
        img.save(
            "{dirname}/{filename}.jpg".format(dirname=OUT_DIR, filename=str(color)))
    except:
        return False


def convert_all_images(paths):
    """生成马赛克块"""
    print("开始生成马赛克块...")
    with ProcessPoolExecutor() as pool:
        pool.map(convert_image, paths)


def find_closiest_hsv(hsv, hsvs):
    """寻找最相近的hsv"""
    similarColor = None
    allowedDiff = ALLOWED_DIFF
    for curColor in hsvs:
        # 计算两个hsv的差值
        diffValue = math.sqrt(sum([(curColor[i]-hsv[i])**2 for i in range(3)]))
        # 如果满足一定的要求
        if diffValue < allowedDiff and curColor[3] < REPEAT:
            allowedDiff = diffValue
            similarColor = curColor
    # 如果不存在颜色最近，抛出异常
    if similarColor is None:
        raise ValueError("没有足够的近似图片，建议添加更多图源，或是增加图片重复使用次数")

    similarColor[3] += 1
    return "({}, {}, {})".format(similarColor[0], similarColor[1], similarColor[2])


def get_hsv_list():
    """获取全部图源值，返回一个列表"""
    hvsList = list()
    # 遍历输出目录
    for filename in os.listdir(OUT_DIR):
        # 获取文件名，不要后缀
        result = re.match(r"\((.+)\)\.jpg", filename)
        hvsValue = result.group(1).split(",")
        # 全部浮点
        hvs = list(map(float, hvsValue))
        # 末尾+0，标记重复次数
        hvs.append(0)
        # 追加
        hvsList.append(hvs)
    return hvsList


def make_pic_by_imgs(img, hsvs):
    """利用小图片制作大图片"""
    width, height = img.size
    # print("Width = {}, Height = {}".format(width, height))

    # 创建一张画布
    background = Image.new('RGB', img.size, (255, 255, 255))
    # 需要小图片的总数
    totalImgs = math.floor((width*height) / SLICE_SIZE**2)
    # 已经使用小图片的数量
    usedImgs = 0
    print("Start composing the pic: ")
    for top in range(0, height, SLICE_SIZE):
        for left in range(0, width, SLICE_SIZE):

            bottom = top + SLICE_SIZE
            right = left + SLICE_SIZE
            # 截取大图片的一个“块”
            curImg = img.crop((left, top, right, bottom))
            # 得到这个图片的hsv值
            hsv = get_avg_hsv(curImg)
            # 找到与“块”hsv值最相近的小图片名
            similarImgName = find_closiest_hsv(hsv, hsvs)
            # 找到这个图片的路径
            similarImgPath = "{dir}/{imgname}.jpg".format(dir=OUT_DIR, imgname=similarImgName)
            try:
                pasteImg = Image.open(similarImgPath)
            except IOError:
                print('创建马赛克块失败')
                raise

            # 打印进度条
            usedImgs += 1
            done = math.floor((usedImgs / totalImgs) * 100)
            r = "\r[{}{}]{}%".format("#"*done, " "*(100-done), done)
            # r = "\rprocessing: {}%".format(done)
            # sys.stdout.write(r)
            # sys.stdout.flush()
            print(r, end="")

            # 将小图片粘贴到画布上
            background.paste(pasteImg, (left, top))

    background.save("pre-dated.jpg")
    return background


def init():
    """初始化配置"""
    print("1. 已经有图片源")
    print("2. 还没有图片源")
    choiceFirst = input("Please enter the num:")
    if choiceFirst == "1":
        pass
    elif choiceFirst == "2":
        threading_main()
    else:
        print("退出程序，不知道你在说啥")
        return False

    print("1. 已经生成马赛克图片")
    print("2. 还未生成马赛克图片")
    choiceSecond = input("Please enter the num:")
    if choiceSecond == "1":
        pass
    elif choiceSecond == "2":
        paths = get_image_paths()
        convert_all_images(paths)
    else:
        print("你要乱输，我要退出（再见脸）")
        return False

    dirname = "{0}/{1}".format(os.path.abspath(os.path.dirname(__file__)), OUT_DIR)
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    return True


if __name__ == "__main__":
    result = init()

    if result:
        img = resize_pic("test.jpg", IMG_WIDTH)
        hvses = get_hsv_list()
        out = make_pic_by_imgs(img, hvses)
        img = Image.blend(out, img, 0.4)
        img.save('out.jpg')