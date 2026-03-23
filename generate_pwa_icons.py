"""
生成 PWA 应用图标
使用 PIL/Pillow 生成不同尺寸的图标
"""
from PIL import Image, ImageDraw, ImageFont

def create_icon(size, output_path):
    """创建指定尺寸的图标"""
    # 创建渐变背景
    img = Image.new('RGB', (size, size), color='#4F46E5')
    draw = ImageDraw.Draw(img)

    # 绘制圆形背景
    margin = size // 10
    draw.ellipse([margin, margin, size - margin, size - margin], fill='#667eea')

    # 绘制📊表情符号（使用文字代替）
    try:
        # 尝试使用中文字体
        font_size = size // 2
        try:
            font = ImageFont.truetype("simhei.ttf", font_size)  # 黑体
        except:
            try:
                font = ImageFont.truetype("msyh.ttc", font_size)  # 微软雅黑
            except:
                font = ImageFont.load_default()

        # 绘制文字
        text = "📊"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size - text_width) // 2
        y = (size - text_height) // 2
        draw.text((x, y), "数", font=font, fill='white')
    except Exception as e:
        print(f"绘制文字失败：{e}")
        # 简单绘制一个图表符号
        center = size // 2
        bar_width = size // 8
        heights = [size // 4, size // 3, size // 2]
        for i, h in enumerate(heights):
            x = center - size // 4 + i * (bar_width + 5)
            y = size - margin - h
            draw.rectangle([x, y, x + bar_width, size - margin], fill='white')

    img.save(output_path, 'PNG')
    print(f"已生成图标：{output_path} ({size}x{size})")

if __name__ == "__main__":
    # 生成 192x192 和 512x512 图标
    create_icon(192, "static/app_icon_192.png")
    create_icon(512, "static/app_icon_512.png")
    print("图标生成完成！")
