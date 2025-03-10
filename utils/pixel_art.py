"""
ピクセルアートモジュール

ドット絵を作成・管理するための機能を提供します。
"""

import pyxel

class PixelArt:
    """
    ピクセルアート（ドット絵）クラス
    
    ドット絵の作成、編集、保存、読み込みなどの機能を提供します。
    """
    
    def __init__(self, width, height):
        """
        ピクセルアートを初期化します。
        
        @param {int} width - ドット絵の幅
        @param {int} height - ドット絵の高さ
        """
        self.width = width
        self.height = height
        self.pixels = [[0 for _ in range(width)] for _ in range(height)]
        
    def set_pixel(self, x, y, color):
        """
        指定した座標にピクセルを設定します。
        
        @param {int} x - X座標
        @param {int} y - Y座標
        @param {int} color - ピクセルの色（Pyxelのカラーコード 0-15）
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = color
            
    def get_pixel(self, x, y):
        """
        指定した座標のピクセルの色を取得します。
        
        @param {int} x - X座標
        @param {int} y - Y座標
        @returns {int} - ピクセルの色
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.pixels[y][x]
        return 0
    
    def fill(self, color):
        """
        すべてのピクセルを指定した色で塗りつぶします。
        
        @param {int} color - 塗りつぶす色
        """
        for y in range(self.height):
            for x in range(self.width):
                self.pixels[y][x] = color
    
    def draw_line(self, x1, y1, x2, y2, color):
        """
        線を描画します。
        
        @param {int} x1 - 開始点のX座標
        @param {int} y1 - 開始点のY座標
        @param {int} x2 - 終了点のX座標
        @param {int} y2 - 終了点のY座標
        @param {int} color - 線の色
        """
        # ブレゼンハムのアルゴリズムを使用
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while True:
            self.set_pixel(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
    
    def draw_rect(self, x, y, w, h, color):
        """
        矩形を描画します。
        
        @param {int} x - 左上のX座標
        @param {int} y - 左上のY座標
        @param {int} w - 幅
        @param {int} h - 高さ
        @param {int} color - 矩形の色
        """
        for i in range(max(0, x), min(x + w, self.width)):
            for j in range(max(0, y), min(y + h, self.height)):
                self.set_pixel(i, j, color)
    
    def draw_circle(self, x, y, radius, color):
        """
        円を描画します。
        
        @param {int} x - 中心のX座標
        @param {int} y - 中心のY座標
        @param {int} radius - 半径
        @param {int} color - 円の色
        """
        for i in range(max(0, x - radius), min(x + radius + 1, self.width)):
            for j in range(max(0, y - radius), min(y + radius + 1, self.height)):
                if (i - x) ** 2 + (j - y) ** 2 <= radius ** 2:
                    self.set_pixel(i, j, color)
    
    def to_pyxel_image(self, img_bank, img_x, img_y):
        """
        Pyxelのイメージバンクにピクセルアートを書き込みます。
        
        @param {int} img_bank - イメージバンク番号 (0-2)
        @param {int} img_x - イメージバンク内のX座標
        @param {int} img_y - イメージバンク内のY座標
        """
        for y in range(self.height):
            for x in range(self.width):
                pyxel.image(img_bank).set(img_x + x, img_y + y, self.pixels[y][x])
    
    def to_string_array(self):
        """
        ピクセルアートを文字列の配列に変換します。
        Pyxelのイメージバンクに直接設定する際に使用できます。
        
        @returns {list} - 文字列の配列
        """
        result = []
        for row in self.pixels:
            line = ""
            for pixel in row:
                line += str(pixel)
            result.append(line)
        return result
    
    @classmethod
    def from_string_array(cls, string_array):
        """
        文字列の配列からピクセルアートを作成します。
        
        @param {list} string_array - 文字列の配列
        @returns {PixelArt} - 作成されたピクセルアート
        """
        if not string_array:
            return cls(0, 0)
        
        height = len(string_array)
        width = len(string_array[0])
        
        art = cls(width, height)
        
        for y, row in enumerate(string_array):
            for x, pixel in enumerate(row):
                if x < width:
                    # 文字を整数に変換
                    try:
                        color = int(pixel) if pixel.isdigit() else 0
                    except ValueError:
                        color = 0
                    art.set_pixel(x, y, color)
        
        return art

    @classmethod
    def create_spaceship(cls, width=16, height=16):
        """
        宇宙船のドット絵を作成します。
        
        @param {int} width - 宇宙船の幅
        @param {int} height - 宇宙船の高さ
        @returns {PixelArt} - 宇宙船のドット絵
        """
        # 宇宙船のドット絵を作成
        spaceship = cls(width, height)
        
        # 基本の宇宙船の形（青色系）を描画
        # 青色を使用（Pyxelのカラーパレットの1=青、12=水色）
        color_main = 1  # 濃い青
        color_light = 12  # 水色
        color_highlight = 7  # 白
        
        # 基本形状（下から上に向かう三角形）
        spaceship.draw_rect(7, 1, 2, 2, color_light)  # 先端
        spaceship.draw_rect(6, 3, 4, 2, color_light)
        spaceship.draw_rect(5, 5, 6, 2, color_main)
        spaceship.draw_rect(4, 7, 8, 3, color_main)
        spaceship.draw_rect(3, 10, 10, 2, color_main)
        spaceship.draw_rect(2, 12, 12, 2, color_main)
        
        # ハイライト
        spaceship.draw_line(7, 1, 8, 1, color_highlight)
        spaceship.set_pixel(7, 2, color_highlight)
        
        # エンジン部分
        spaceship.set_pixel(3, 14, color_light)
        spaceship.set_pixel(4, 14, color_light)
        spaceship.set_pixel(11, 14, color_light)
        spaceship.set_pixel(12, 14, color_light)
        spaceship.set_pixel(6, 14, color_highlight)
        spaceship.set_pixel(7, 14, color_highlight)
        spaceship.set_pixel(8, 14, color_highlight)
        spaceship.set_pixel(9, 14, color_highlight)
        
        return spaceship

    @classmethod
    def create_beam(cls, width=3, height=8):
        """
        ビームのドット絵を作成します。
        
        @param {int} width - ビームの幅
        @param {int} height - ビームの高さ
        @returns {PixelArt} - ビームのドット絵
        """
        # ビームのドット絵を作成
        beam = cls(width, height)
        
        # 青色系のビーム
        color_core = 7   # 白色（中心）
        color_outer = 12  # 水色（外側）
        
        # 中心の白い部分
        for y in range(height):
            beam.set_pixel(1, y, color_core)
        
        # 外側の水色部分
        for y in range(height):
            beam.set_pixel(0, y, color_outer)
            beam.set_pixel(2, y, color_outer)
        
        return beam 