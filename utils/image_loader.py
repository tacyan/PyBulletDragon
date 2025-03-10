"""
画像ローダーモジュール

画像ファイルを読み込み、Pyxelのリソースに変換する機能を提供します。
"""

import pyxel
from PIL import Image
import os
import sys
import numpy as np
import math

# デバッグモード（Trueにすると詳細な情報を出力）
DEBUG = True

class ImageLoader:
    """
    画像ローダークラス
    
    画像データをPyxelのリソースに変換するための機能を提供します。
    """
    
    # Pyxelの16色パレット（RGB値）
    PYXEL_PALETTE = [
        (0, 0, 0),        # 0: 黒
        (29, 43, 83),     # 1: 紺色
        (126, 37, 83),    # 2: 紫
        (0, 135, 81),     # 3: 緑
        (171, 82, 54),    # 4: 茶色
        (95, 87, 79),     # 5: 暗い灰色
        (194, 195, 199),  # 6: 明るい灰色
        (255, 241, 232),  # 7: 白
        (255, 0, 77),     # 8: 赤
        (255, 163, 0),    # 9: オレンジ
        (255, 236, 39),   # 10: 黄色
        (0, 228, 54),     # 11: 黄緑
        (41, 173, 255),   # 12: 水色
        (131, 118, 156),  # 13: インディゴ
        (255, 119, 168),  # 14: ピンク
        (255, 204, 170)   # 15: 桃色
    ]
    
    @staticmethod
    def get_closest_color_index(r, g, b):
        """
        RGB値に最も近いPyxelパレットの色のインデックスを返します。
        
        @param {number} r - 赤成分 (0-255)
        @param {number} g - 緑成分 (0-255)
        @param {number} b - 青成分 (0-255)
        @returns {number} - パレットのインデックス (0-15)
        """
        min_distance = float('inf')
        closest_index = 0
        
        for i, color in enumerate(ImageLoader.PYXEL_PALETTE):
            # ユークリッド距離でRGB空間における色の距離を計算
            distance = math.sqrt(
                (r - color[0]) ** 2 + 
                (g - color[1]) ** 2 + 
                (b - color[2]) ** 2
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_index = i
                
        return closest_index
    
    @staticmethod
    def load_player_png(bank, x, y, debug=DEBUG):
        """
        player.png画像をPyxelのリソースに変換します。
        
        @param {number} bank - イメージバンク番号
        @param {number} x - イメージバンク内のX座標
        @param {number} y - イメージバンク内のY座標
        @param {boolean} debug - デバッグ情報を出力するかどうか
        @returns {tuple} - 画像の高さと幅、読み込み成功の真偽値
        """
        # 複数の可能性のあるパスを試す
        possible_paths = [
            os.path.join("resources", "player.png"),
            os.path.join(".", "resources", "player.png"),
            os.path.join("..", "resources", "player.png"),
            "player.png"
        ]
        
        img_path = None
        for path in possible_paths:
            if os.path.exists(path):
                img_path = path
                if debug:
                    print(f"画像ファイルが見つかりました: {path}")
                break
        
        if img_path is None:
            if debug:
                print("画像ファイルが見つかりません。以下のパスを検索しました:")
                for path in possible_paths:
                    print(f"  - {os.path.abspath(path)}")
                print("現在の作業ディレクトリ:", os.getcwd())
            return ImageLoader.load_space_shuttle(bank, x, y), False
        
        try:
            # PILでイメージを開く
            img = Image.open(img_path)
            
            # サイズチェック
            width, height = img.size
            if width > 64 or height > 64:
                if debug:
                    print(f"警告: 画像サイズが大きすぎます ({width}x{height}). 64x64以下を推奨します。")
                # アスペクト比を維持してリサイズ
                ratio = min(64 / width, 64 / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
                width, height = img.size
                if debug:
                    print(f"画像をリサイズしました: {width}x{height}")
            
            if debug:
                print(f"画像情報: サイズ={width}x{height}, モード={img.mode}")
            
            # モードに応じて変換
            if img.mode != 'RGBA':
                if debug:
                    print(f"画像モードを{img.mode}からRGBAに変換します")
                if img.mode == 'RGB':
                    # RGBからRGBAに変換（透明度は最大に）
                    rgba = Image.new("RGBA", img.size)
                    rgba.paste(img, (0, 0))
                    img = rgba
                else:
                    # その他のモードはRGBAに変換
                    img = img.convert('RGBA')
            
            # イメージバンクをクリア（重要）
            for clear_y in range(height * 2):  # 2フレーム分の領域をクリア
                for clear_x in range(width):
                    pyxel.images[bank].pset(x + clear_x, y + clear_y, 0)
            
            # Pyxelのイメージバンクに画像データをセット
            transparent_pixels = 0
            colored_pixels = 0
            
            for py in range(height):
                for px in range(width):
                    r, g, b, a = img.getpixel((px, py))
                    
                    # 透明度処理（より細かく）
                    if a < 50:  # ほぼ透明
                        color = 0
                        transparent_pixels += 1
                    else:
                        # 半透明の場合は色を暗くする
                        if 50 <= a < 200:
                            factor = a / 255.0
                            r = int(r * factor)
                            g = int(g * factor)
                            b = int(b * factor)
                        
                        # 最も近い色を見つける
                        color = ImageLoader.get_closest_color_index(r, g, b)
                        colored_pixels += 1
                    
                    # Pyxelのイメージバンクにピクセルをセット
                    pyxel.images[bank].pset(x + px, y + py, color)
            
            if debug:
                print(f"Pyxelリソースに変換: 透明ピクセル={transparent_pixels}, 色付きピクセル={colored_pixels}")
            
            # 2枚目のフレームを作成（エンジン炎アニメーション用）
            # 元画像の完全なコピー（ピクセルごとに確実にコピー）
            for py in range(height):
                for px in range(width):
                    color = pyxel.images[bank].pget(x + px, y + py)
                    # 必ず2枚目のフレームにコピーする
                    pyxel.images[bank].pset(x + px, y + height + py, color)
            
            if debug:
                print(f"2枚目のフレームをコピーしました: y={y+height}, 高さ={height}")
            
            # エンジン部分（下部中央）に炎エフェクトを追加
            engine_area_width = width // 3
            engine_start_x = x + (width - engine_area_width) // 2
            engine_end_x = engine_start_x + engine_area_width
            
            # 1枚目のエンジン炎（小さめ）
            engine_y1 = y + height - 1  # 1枚目の画像の下部
            for px in range(engine_start_x, engine_end_x):
                # 中央に近いほど長い炎に
                distance_from_center = abs(px - (engine_start_x + engine_area_width//2))
                if distance_from_center < engine_area_width // 4:
                    flame_color = 10  # 黄色（中央）
                    pyxel.images[bank].pset(px, engine_y1, flame_color)
                elif distance_from_center < engine_area_width // 2:
                    flame_color = 9  # オレンジ（周辺）
                    pyxel.images[bank].pset(px, engine_y1, flame_color)
            
            # 2枚目のエンジン炎（長め）
            engine_y2 = y + height * 2 - 1  # 2枚目の画像の下部
            for px in range(engine_start_x, engine_end_x):
                # 中央に近いほど長い炎に
                distance_from_center = abs(px - (engine_start_x + engine_area_width//2))
                flame_length = max(1, 3 - distance_from_center // 2)
                
                for flame_y in range(flame_length):
                    # 炎の色（中央は黄色、外側はオレンジ）
                    flame_color = 10 if distance_from_center < engine_area_width // 4 else 9
                    pyxel.images[bank].pset(px, engine_y2 - flame_y, flame_color)
            
            if debug:
                print(f"エンジン炎を追加しました: 位置1={engine_y1}, 位置2={engine_y2}")
                print(f"アニメーションフレームを作成: 高さ={height*2}, 幅={width}")
                
            return (height, width), True
            
        except Exception as e:
            if debug:
                print(f"画像ロード中にエラーが発生しました: {e}")
                import traceback
                traceback.print_exc()
            # エラー時はデフォルトのスペースシャトルを返す
            return ImageLoader.load_space_shuttle(bank, x, y), False
    
    @staticmethod
    def load_space_shuttle(bank, x, y):
        """
        スペースシャトル画像をPyxelのリソースに直接描画します。
        
        @param {number} bank - イメージバンク番号
        @param {number} x - イメージバンク内のX座標
        @param {number} y - イメージバンク内のY座標
        @returns {tuple} - 画像の高さと幅
        """
        # 添付されたスペースシャトル画像データ
        # 色コード: 0=透明, 1=青, 5=グレー, 7=白, 8=濃いグレー, 2=赤
        shuttle_pixels = [
            "00000007700000000",
            "00000075570000000",
            "00000755557000000",
            "00000755557000000",
            "00000755557000000",
            "00007555555700000",
            "00007555555700000",
            "00075557555570000",
            "00075557555570000",
            "00755555555557000",
            "00755555555557000",
            "07555578785557000",
            "07555578785557000",
            "07555555555557000",
            "07555555555557000",
            "07555555555557000",
            "17555555555557100",
            "17555522225557100",
            "17555555555557100",
            "17555555555557100",
            "17555555555557100",
            "17555555555557100",
            "01755555555571000",
            "01755555555571000",
            "00177777777710000"
        ]
        
        # ピクセル情報をPyxelのイメージバンクに直接設定
        for y_offset, row in enumerate(shuttle_pixels):
            for x_offset, pixel in enumerate(row):
                color = 0  # デフォルトは透明
                
                if pixel == "1":
                    color = 1  # 青色
                elif pixel == "2":
                    color = 8  # 赤色
                elif pixel == "5":
                    color = 6  # グレー
                elif pixel == "7":
                    color = 7  # 白色
                elif pixel == "8":
                    color = 5  # 濃いグレー
                
                pyxel.images[bank].pset(x + x_offset, y + y_offset, color)
        
        # 2枚目のフレーム（エンジン炎アニメーション用）
        shuttle_height = len(shuttle_pixels)
        shuttle_width = len(shuttle_pixels[0])
        
        # 1枚目をコピー
        for y_offset in range(shuttle_height):
            for x_offset in range(shuttle_width):
                color = pyxel.images[bank].pget(x + x_offset, y + y_offset)
                pyxel.images[bank].pset(x + x_offset, y + shuttle_height + y_offset, color)
        
        # エンジン炎を追加（2枚目の下部）
        for px in range(x + 7, x + 11):
            pyxel.images[bank].pset(px, y + shuttle_height * 2 - 2, 10)  # 黄色
            pyxel.images[bank].pset(px, y + shuttle_height * 2 - 1, 9)   # オレンジ
        
        if DEBUG:
            print(f"デフォルトのスペースシャトルを読み込みました: 高さ={shuttle_height}, 幅={shuttle_width}")
        
        return (shuttle_height, shuttle_width), True
    
    @staticmethod
    def load_bullet(bank, x, y):
        """
        シャトルの弾をPyxelのリソースに直接描画します。
        
        @param {number} bank - イメージバンク番号
        @param {number} x - イメージバンク内のX座標
        @param {number} y - イメージバンク内のY座標
        @returns {tuple} - 画像の高さと幅
        """
        # シャトルの弾の画像データ
        bullet_pixels = [
            "00100",
            "01710",
            "17771",
            "17771",
            "01710",
            "00100"
        ]
        
        # ピクセル情報をPyxelのイメージバンクに直接設定
        for y_offset, row in enumerate(bullet_pixels):
            for x_offset, pixel in enumerate(row):
                color = 0  # デフォルトは透明
                
                if pixel == "1":
                    color = 12  # 水色
                elif pixel == "7":
                    color = 7  # 白色
                
                pyxel.images[bank].pset(x + x_offset, y + y_offset, color)
        
        return len(bullet_pixels), len(bullet_pixels[0])  # 高さと幅を返す
    
    @staticmethod
    def load_option(bank, x, y):
        """
        オプション（サブウェポン）をPyxelのリソースに直接描画します。
        
        @param {number} bank - イメージバンク番号
        @param {number} x - イメージバンク内のX座標
        @param {number} y - イメージバンク内のY座標
        @returns {tuple} - 画像の高さと幅
        """
        # オプションの画像データ（小型のスペースシャトル）
        option_pixels = [
            "00700",
            "07570",
            "75557",
            "75557",
            "07570",
            "00700"
        ]
        
        # ピクセル情報をPyxelのイメージバンクに直接設定
        for y_offset, row in enumerate(option_pixels):
            for x_offset, pixel in enumerate(row):
                color = 0  # デフォルトは透明
                
                if pixel == "5":
                    color = 6  # グレー
                elif pixel == "7":
                    color = 7  # 白色
                
                pyxel.images[bank].pset(x + x_offset, y + y_offset, color)
        
        return len(option_pixels), len(option_pixels[0])  # 高さと幅を返す
    
    @staticmethod
    def verify_resources(bank):
        """
        リソースが正しく読み込まれているか検証します。
        
        @param {number} bank - 検証するイメージバンク番号
        @returns {boolean} - 検証結果
        """
        if DEBUG:
            print(f"イメージバンク {bank} の内容を検証中...")
            non_zero_pixels = 0
            for y in range(256):
                for x in range(256):
                    if pyxel.images[bank].pget(x, y) != 0:
                        non_zero_pixels += 1
            print(f"非透明ピクセル数: {non_zero_pixels}")
            return non_zero_pixels > 0
        return True 