import os
import json
import webbrowser
from tkinter import Tk, Label, Button, Entry, filedialog, messagebox, colorchooser
from tkinter import ttk, StringVar
from PIL import Image, ImageDraw, ImageFont, ImageOps

def is_chinese(char):
    """判断一个字符是否是中文"""
    return '\u4e00' <= char <= '\u9fff'

class WatermarkApp:
    def __init__(self, master):
        self.master = master
        master.title("批量图片加水印")

        # 水印内容输入框
        self.label_text = Label(master, text="输入水印内容：")
        self.label_text.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.entry_text = Entry(master, width=50)
        self.entry_text.insert(0, "MU Group Leo: +86 13819858718")  # 默认水印内容
        self.entry_text.grid(row=0, column=1, padx=10, pady=5)

        # 字体大小输入框
        self.label_font_size = Label(master, text="输入字体大小：")
        self.label_font_size.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.entry_font_size = Entry(master, width=10)
        self.entry_font_size.insert(0, "40")  # 默认字体大小
        self.entry_font_size.grid(row=1, column=1, padx=10, pady=5)

        # 透明度输入框
        self.label_opacity = Label(master, text="输入透明度 (0-100)：")
        self.label_opacity.grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.entry_opacity = Entry(master, width=10)
        self.entry_opacity.insert(0, "100")  # 默认透明度为100%
        self.entry_opacity.grid(row=2, column=1, padx=10, pady=5)

        # 设置默认焦点到水印内容输入框
        self.entry_text.focus_set()

        # 颜色选择
        self.label_color = Label(master, text="选择水印颜色：")
        self.label_color.grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.color_button = Button(master, text="选择颜色", command=self.choose_color)
        self.color_button.grid(row=3, column=1, padx=10, pady=5)
        self.color = (255, 255, 0)  # 默认颜色黄色

        # 位置选择
        self.label_position = Label(master, text="选择水印位置：")
        self.label_position.grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.position_var = StringVar(value="center")
        self.position_options = ["左上角", "右上角", "左下角", "右下角", "中心"]
        self.position_dropdown = ttk.Combobox(master, textvariable=self.position_var, values=self.position_options, state="readonly")
        self.position_dropdown.grid(row=4, column=1, padx=10, pady=5)

        self.label_folder = Label(master, text="选择文件夹以批量添加水印")
        self.label_folder.grid(row=5, column=0, sticky="w", padx=10, pady=5)

        self.select_button = Button(master, text="选择文件夹", command=self.select_folder)
        self.select_button.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        # 预览按钮
        self.preview_button = Button(master, text="预览水印", command=self.preview_watermark)
        self.preview_button.grid(row=5, column=1, padx=10, pady=5, sticky="e")

        # 进度条和详情
        self.progress = ttk.Progressbar(master, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=6, column=0, columnspan=2, padx=10, pady=5)
        self.progress_label = Label(master, text="")
        self.progress_label.grid(row=7, column=0, columnspan=2, padx=10, pady=5)

        # 开始处理按钮
        self.process_button = Button(master, text="开始处理", command=self.add_watermarks, state="disabled", bg="green", fg="white", width=30, font=("Arial", 12), disabledforeground="white")
        self.process_button.grid(row=8, column=0, columnspan=2, pady=20)

        # 保存设置按钮
        self.save_button = Button(master, text="保存设置", command=self.save_settings)
        self.save_button.grid(row=9, column=0, columnspan=2, pady=5)

        # 退出按钮
        self.exit_button = Button(master, text="退出", command=self.quit_app, width=20, height=2)
        self.exit_button.grid(row=10, column=1, sticky="e", pady=10)

        self.selected_folder = ""
        self.output_folder = ""

        # 尝试加载设置
        self.load_settings()

    def choose_color(self):
        color_code = colorchooser.askcolor(title="选择水印颜色")
        if color_code:
            self.color = color_code[0]

    def select_folder(self):
        self.selected_folder = filedialog.askdirectory()
        if self.selected_folder:
            self.process_button.config(state="normal")
            self.label_folder.config(text=f"已选择文件夹：{self.selected_folder}")

    def calculate_position(self, image_size, watermark_size, position):
        """根据用户选择的水印位置计算水印的左上角坐标"""
        if position == "左上角":
            return 10, 10
        elif position == "右上角":
            return image_size[0] - watermark_size[0] - 10, 10
        elif position == "左下角":
            return 10, image_size[1] - watermark_size[1] - 10
        elif position == "右下角":
            return image_size[0] - watermark_size[0] - 10, image_size[1] - watermark_size[1] - 10
        else:  # 中心
            return (image_size[0] - watermark_size[0]) // 2, (image_size[1] - watermark_size[1]) // 2

    def get_font_style(self, font_name, font_size):
        """返回字体样式"""
        font_style = ImageFont.truetype(font_name, font_size)
        return font_style

    def draw_text(self, draw, position, text, font, color, opacity):
        """处理绘制文本及样式"""
        draw.text(position, text, font=font, fill=(*color, opacity))

    def preview_watermark(self):
        if not self.selected_folder:
            messagebox.showwarning("未选择文件夹", "请先选择一个文件夹！")
            return

        # 获取水印内容、字体大小和透明度
        watermark_text = self.entry_text.get()
        font_size = int(self.entry_font_size.get())
        opacity = int(self.entry_opacity.get()) * 255 // 100  # 将0-100的值转换为0-255
        position = self.position_var.get()

        # 使用系统内置字体
        font_chinese = self.get_font_style("simsun.ttc", font_size)  # 中文字体
        font_english = self.get_font_style("arial.ttf", font_size)   # 英文字体

        # 选择一张图片进行预览
        image_files = [f for f in os.listdir(self.selected_folder) if f.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        if not image_files:
            messagebox.showwarning("没有找到图片", "选择的文件夹中没有找到图片。")
            return

        preview_image_path = os.path.join(self.selected_folder, image_files[0])
        image = Image.open(preview_image_path).convert("RGBA")

        # 创建水印层
        watermark_layer = Image.new("RGBA", image.size)
        draw = ImageDraw.Draw(watermark_layer)

        # 计算文本宽度和高度
        total_width = 0
        total_height = 0
        max_width = image.size[0]

        x, y = 0, 0

        for char in watermark_text:
            # 根据字符类型选择字体
            current_font = font_chinese if is_chinese(char) else font_english
            char_width, char_height = draw.textbbox((0, 0), char, font=current_font)[2:4]

            if x + char_width > max_width:
                x = 0
                y += char_height
            x += char_width
            total_width = max(total_width, x)
            total_height = y + char_height

        # 计算中心位置
        x_start, y_start = self.calculate_position(image.size, (total_width, total_height), position)

        x = x_start
        y = y_start

        # 再次绘制水印，确保位置正确
        for char in watermark_text:
            current_font = font_chinese if is_chinese(char) else font_english
            char_width, char_height = draw.textbbox((0, 0), char, font=current_font)[2:4]

            if x + char_width > max_width:
                x = x_start
                y += char_height

            self.draw_text(draw, (x, y), char, current_font, self.color, opacity)
            x += char_width

        # 合并水印层和原图
        preview_image = Image.alpha_composite(image, watermark_layer)

        # 显示预览
        preview_image.show()

    def add_watermarks(self):
        if not self.selected_folder:
            messagebox.showwarning("未选择文件夹", "请先选择一个文件夹！")
            return

        # 获取水印内容、字体大小、透明度、颜色和位置
        watermark_text = self.entry_text.get()
        font_size = int(self.entry_font_size.get())
        opacity = int(self.entry_opacity.get()) * 255 // 100  # 将0-100的值转换为0-255
        position = self.position_var.get()

        # 使用系统内置字体
        font_chinese = self.get_font_style("simsun.ttc", font_size)  # 中文字体
        font_english = self.get_font_style("arial.ttf", font_size)   # 英文字体

        # 创建输出文件夹
        self.output_folder = os.path.join(self.selected_folder, "Watermarked_Images")
        os.makedirs(self.output_folder, exist_ok=True)

        # 获取图片总数并初始化进度条
        image_files = [f for f in os.listdir(self.selected_folder) if f.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
        total_images = len(image_files)
        self.progress["maximum"] = total_images

        # 处理图片
        for i, filename in enumerate(image_files):
            image_path = os.path.join(self.selected_folder, filename)
            image = Image.open(image_path).convert("RGBA")

            # 创建水印层
            watermark_layer = Image.new("RGBA", image.size)
            draw = ImageDraw.Draw(watermark_layer)

            # 计算文本宽度和高度
            total_width = 0
            total_height = 0
            max_width = image.size[0]

            x, y = 0, 0

            for char in watermark_text:
                # 根据字符类型选择字体
                current_font = font_chinese if is_chinese(char) else font_english
                char_width, char_height = draw.textbbox((0, 0), char, font=current_font)[2:4]

                if x + char_width > max_width:
                    x = 0
                    y += char_height
                x += char_width
                total_width = max(total_width, x)
                total_height = y + char_height

            # 计算中心位置
            x_start, y_start = self.calculate_position(image.size, (total_width, total_height), position)

            x = x_start
            y = y_start

            # 再次绘制水印，确保位置正确
            for char in watermark_text:
                current_font = font_chinese if is_chinese(char) else font_english
                char_width, char_height = draw.textbbox((0, 0), char, font=current_font)[2:4]

                if x + char_width > max_width:
                    x = x_start
                    y += char_height

                self.draw_text(draw, (x, y), char, current_font, self.color, opacity)
                x += char_width

            # 合并水印层和原图
            watermarked_image = Image.alpha_composite(image, watermark_layer)

            # 保存图片
            output_path = os.path.join(self.output_folder, filename)
            watermarked_image.convert("RGB").save(output_path)

            # 更新进度条和详情
            self.progress["value"] = i + 1
            self.progress_label.config(text=f"正在处理: {filename} ({i + 1}/{total_images})")
            self.master.update_idletasks()

        messagebox.showinfo("完成", f"所有图片已处理完毕，保存至：{self.output_folder}")
        self.progress["value"] = 0  # 重置进度条
        self.progress_label.config(text="")
        self.open_output_folder()

    def save_settings(self):
        settings = {
            "watermark_text": self.entry_text.get(),
            "font_size": self.entry_font_size.get(),
            "opacity": self.entry_opacity.get(),
            "color": self.color,
            "position": self.position_var.get(),
        }
        with open("settings.json", "w") as f:
            json.dump(settings, f)
        self.master.after(100, lambda: messagebox.showinfo("设置已保存", "水印设置已保存成功！"))

    def load_settings(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                settings = json.load(f)
                self.entry_text.delete(0, 'end')
                self.entry_text.insert(0, settings.get("watermark_text", ""))
                self.entry_font_size.delete(0, 'end')
                self.entry_font_size.insert(0, settings.get("font_size", "40"))
                self.entry_opacity.delete(0, 'end')
                self.entry_opacity.insert(0, settings.get("opacity", "100"))
                self.color = tuple(settings.get("color", (255, 255, 0)))
                self.position_var.set(settings.get("position", "center"))
                self.master.after(100, lambda: messagebox.showinfo("设置已加载", "水印设置已成功加载！"))

    def open_output_folder(self):
        webbrowser.open(self.output_folder)

    def quit_app(self):
        self.master.quit()
        self.master.destroy()


if __name__ == "__main__":
    root = Tk()
    app = WatermarkApp(root)
    root.mainloop()
