from PIL import Image, ImageFont, ImageDraw, ImageEnhance
import os, cv2, re
from tqdm import tqdm
import numpy as np


class AsciiTool():

    def __init__(self,
                 img_to_ascii: str,
                 output_name: str,
                 font: str = "UbuntuMono-B.ttf",
                 font_size: int = 15,
                 luminance_list: str = r" `.-':,^=;><+!rc*z?sLTv)J7(Fi{C}fI31tlbUAKXHm8RD#$Bg0MNWQ%&@",
                 compression: int = 5,
                 fill: tuple = (255, 255, 255),
                 background: tuple = (0, 0, 0),
                 output_path: str = ".\\AsciiArtOutputs",
                 edge_detection_strength: int = 1,
                 in_color: bool = False,
                 edge_detection: bool = False,
                 variable_range: int = None,
                 scale: int = 1,
                 variable_range_step_size: int = 1
                 ):

        self.luminance_list = [char for char in luminance_list]
        self.luminance_list_len = len(self.luminance_list)
        self.font_size = font_size
        self.font_path = font
        self.font = ImageFont.truetype(font, font_size)
        self.compression = compression
        self.output_name = output_name
        self.img_to_ascii = Image.open(img_to_ascii)
        self.fill = fill
        self.background = background
        self.output_path = output_path
        self.edge_detection_strength = edge_detection_strength
        self.in_color = in_color
        self.edge_detection = edge_detection
        self.variable_range = variable_range
        self.variable_range_step_size = variable_range_step_size
        self.scale = scale
    
    def drawing(self, to_draw, background, fill, name, count, output_path):
        os.makedirs(output_path, exist_ok=True)
        to_draw = to_draw.rstrip("\n")
        
        bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), to_draw, font=self.font)
        width = int((bbox[2] - bbox[0])/self.scale)
        height = int((bbox[3] - bbox[1])/self.scale)
        img = Image.new('RGB', (width, height), background)
        draw = ImageDraw.Draw(img)
        draw.mode = "L"

        per_char = (width/len(to_draw.split("\n")[0]))
        per_row = (height/len(to_draw.split("\n")))

        get_fill = (lambda r, ic: self.colors[r][ic]) if self.in_color else (lambda r, ic: self.fill)
        if self.variable_range:
            
            fonts = [ImageFont.truetype(font=self.font_path, size=abs(self.variable_range+x))
                      for x in range(self.font_size,
                                      abs(self.variable_range),
                                      self.variable_range_step_size)]
            
        for r, row in tqdm(enumerate(to_draw.split("\n")), "Drawing Row"): 
            ic = 0
            for i, char in enumerate(row):
                fill = get_fill(r, ic)
                font = fonts[min(int(self.luminance[r][ic-1] * len(fonts)), len(fonts)-1)] if (
                    self.variable_range
                    ) else self.font
                draw.text(xy=(per_char*i,r*per_row), text=char, fill=fill, font=font)
                if i%2:
                    ic += 1
        img = ImageEnhance.Brightness(img).enhance(1)
        img.save(fr"{output_path}\\{count}{name}.png") 
    
    def map_edges_to_ascii(self):
        img = cv2.imread(rf"{self.output_path}\\intermediate_files\\intermediate.png", cv2.IMREAD_GRAYSCALE)
        grad_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=3)
        h, w = grad_x.shape
        edge_list = []
    
        for i in range(h):
            line = []
            for j in range(w):
                gx = grad_x[i, j]
                gy = grad_y[i, j]
                magnitude = np.sqrt(gx**2 + gy**2)
                if magnitude < self.edge_detection_strength:
                    line.append(" ")
                else:
                    angle = np.arctan2(gy, gx)  # Compute gradient direction
                    if -np.pi / 8 <= angle <= np.pi / 8:
                        line.append("|")  # Vertical edge
                    elif np.pi / 8 < angle < 5 * np.pi / 8:
                        line.append("/")  # Diagonal up-right
                    elif -5 * np.pi / 8 < angle < -np.pi / 8:
                        line.append("\\")  # Diagonal down-right
                    else:
                        line.append("_")  # Horizontal edge
            edge_list.append(" ".join(line))
        edges = "\n".join(edge_list)
        with open(f"{self.output_path}\\{self.count}{self.fill}EDGETEXT{self.output_name}.txt", 'w') as file:
            file.write(" ".join(edges))
        self.drawing(edges, self.background, self.fill, (self.output_name + "edge"), self.count, self.output_path)
        ascii_withEdges = []
        ascii_art_split = self.ascii_art.split("\n")
        edges_split = edges.split("\n")
        for y in range(min(len(ascii_art_split),len(edges_split))):
            new_line = ""
            for x in range(min(len(ascii_art_split[y]), len(edges_split[y]))):
                if edges_split[y][x] not in [" ", "\n"]:
                    new_line += edges_split[y][x]
                else:
                    new_line += ascii_art_split[y][x]
            ascii_withEdges.append(new_line)
        ascii_withEdges = "\n".join(ascii_withEdges)
        self.ascii_art = ascii_withEdges

    def generate(self, word=None):
        rgb_img = self.img_to_ascii.convert('RGB')
        rgb_img.thumbnail((rgb_img.width/self.compression, rgb_img.height/self.compression))
        self.ascii_art = ""

        self.count = 1
        while os.path.exists(f"{self.output_path}\\{self.count}{self.fill}TEXT{self.output_name}.txt"):
            self.count += 1

        ascii_art_line = []
        if word != None:
            word_list = list(re.sub(" +", " ", word.replace("\n", " ").rstrip()))
            word_len = len(word_list)
            word_index = 0

        if self.in_color: self.colors = []
        if self.variable_range: self.luminance = []
        for y in range(rgb_img.height):
            text_line = []
            if self.variable_range: luminance_line = []
            if self.in_color: color_row = []

            for x in range(rgb_img.width):
                pixel = rgb_img.getpixel((x, y))
                luminance = ((0.2126*pixel[0]) + (0.7152*pixel[1]) + (0.0722*pixel[2])) / 256

                if self.in_color: color_row.append(pixel)
                if self.variable_range: luminance_line.append(luminance)

                if word:
                    text_line.append(word_list[word_index])
                    word_index = (word_index + 1) % word_len
                else:
                    index = min(int(luminance * self.luminance_list_len), self.luminance_list_len-1)
                    text_line.append(self.luminance_list[index])

            if self.variable_range: self.luminance.append(luminance_line)
            if self.in_color: self.colors.append(color_row)
            
            ascii_art_line.append(" ".join(text_line))
        self.ascii_art = "\n".join(ascii_art_line)
        with open(f"{self.output_path}\\{self.count}{self.fill}TEXT{self.output_name}.txt", 'w') as file:
            file.writelines(self.ascii_art)

        if self.edge_detection == True:
            os.makedirs(self.output_path, exist_ok=True)
            os.makedirs(self.output_path+r"\\intermediate_files", exist_ok=True)
            rgb_img.save(rf'{self.output_path}\\intermediate_files\\intermediate.png', 'png')
            self.map_edges_to_ascii()

        self.drawing(self.ascii_art, self.background, self.fill, self.output_name, self.count, self.output_path)

def main(input):
    generator = AsciiTool(input, 
                            'soup', 
                            compression = (5), 
                            in_color=True, 
                            edge_detection=False, 
                            font_size=15, 
                            edge_detection_strength=200,
                            font=r"UbuntuMono-B.ttf",
                            scale=2,
                            variable_range= 100,
                            variable_range_step_size=20,)
    # generator.generate()
    generator.generate(".")
if __name__ == "__main__":
    import time
    start_time = time.time()
    main(r"Ascii Art inputs\Klimt_-_Der_Kuss_-_The_Kiss.jpg")
    print(f"Time: {time.time()-start_time}")