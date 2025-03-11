"""
画像ローダーモジュール

画像ファイルを読み込み、Pyxelのリソースに変換する機能を提供します。
"""

import pyxel
import os
import sys
import math

# デバッグモード（Trueにすると詳細な情報を出力）
DEBUG = True

# Pyodide環境でPillowをロードするための関数
def ensure_pil_available():
    """
    Pillowが利用可能であることを確認します。
    Pyodide環境では必要に応じて動的にインストールします。
    
    @returns {boolean} - Pillowが利用可能になったかどうか
    """
    try:
        # すでにインポートできる場合は何もしない
        from PIL import Image
        return True
    except ImportError:
        # Pyodide環境かどうか確認
        is_pyodide = 'pyodide' in sys.modules
        
        if is_pyodide:
            if DEBUG:
                print("Pyodide環境を検出しました。Pillowをインストールします...")
            
            try:
                # Pyodideの場合、micropipを使ってPillowをインストール
                import micropip
                import asyncio
                
                async def install_pillow():
                    await micropip.install('pillow')
                    if DEBUG:
                        print("Pillowのインストールが完了しました")
                
                # 非同期関数を実行
                asyncio.ensure_future(install_pillow())
                
                # インストールを待機
                import time
                for i in range(5):  # 最大5秒待機
                    time.sleep(1)
                    try:
                        from PIL import Image
                        if DEBUG:
                            print("Pillowが正常にインポートできるようになりました")
                        return True
                    except ImportError:
                        if DEBUG:
                            print(f"Pillowのインポート待機中... {i+1}秒経過")
                
                if DEBUG:
                    print("Pillowのインストールは成功しましたが、すぐにはインポートできません。")
                    print("この後の操作で再度Pillowのインポートを試みます。")
                return False
                
            except Exception as e:
                if DEBUG:
                    print(f"Pillowのインストール中にエラーが発生しました: {e}")
                return False
        else:
            if DEBUG:
                print("PIL/Pillowがインストールされていません。一部の機能が制限されます。")
            return False

# PILの可用性を確認
pil_available = ensure_pil_available()

# PILがなくても使えるように必要なnumpyを代替実装
try:
    import numpy as np
except ImportError:
    # numpyが利用できない環境用の簡易実装
    class NumpySubstitute:
        def array(self, data):
            return data
    np = NumpySubstitute()

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
            # ユークリッド距離でRGB空間における色の距離を計算（改良版）
            # 人間の目の感度を考慮した重み付け
            # 人間の目は緑に最も敏感で、次に赤、青の順
            r_weight = 0.3
            g_weight = 0.59
            b_weight = 0.11
            
            # 重み付きユークリッド距離
            distance = math.sqrt(
                r_weight * (r - color[0]) ** 2 + 
                g_weight * (g - color[1]) ** 2 + 
                b_weight * (b - color[2]) ** 2
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_index = i
                
        return closest_index
    
    @staticmethod
    def enhance_contrast(r, g, b):
        """
        RGBの値のコントラストを強調します。
        小さな違いを強調して、Pyxelのパレットに変換した際の視認性を向上させます。
        
        @param {number} r - 赤成分 (0-255)
        @param {number} g - 緑成分 (0-255)
        @param {number} b - 青成分 (0-255)
        @returns {tuple} - 強調されたRGB値
        """
        # コントラスト強調のためのファクタ（1.0より大きいと強調）
        contrast_factor = 1.2
        
        # コントラスト調整の処理
        r = min(255, max(0, int(((r / 255.0 - 0.5) * contrast_factor + 0.5) * 255)))
        g = min(255, max(0, int(((g / 255.0 - 0.5) * contrast_factor + 0.5) * 255)))
        b = min(255, max(0, int(((b / 255.0 - 0.5) * contrast_factor + 0.5) * 255)))
        
        return r, g, b
    
    @staticmethod
    def debug_save_pixel_map(bank, x, y, width, height):
        """
        イメージバンクの指定領域のピクセルマップをテキストファイルとして保存します（デバッグ用）。
        
        @param {number} bank - イメージバンク番号
        @param {number} x - 左上X座標
        @param {number} y - 左上Y座標
        @param {number} width - 幅
        @param {number} height - 高さ
        """
        if not DEBUG:
            return
            
        try:
            with open("pixel_map.txt", "w") as f:
                for py in range(height):
                    line = ""
                    for px in range(width):
                        color = pyxel.images[bank].pget(x + px, y + py)
                        line += str(color)
                    f.write(line + "\n")
                f.write(f"サイズ: {width}x{height}\n")
            print("ピクセルマップを pixel_map.txt に保存しました")
        except Exception as e:
            print(f"ピクセルマップの保存中にエラーが発生しました: {e}")
    
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
        
        # PILを使用して画像を処理
        global pil_available  # 変数使用前にグローバル宣言を行う
        if not pil_available:
            # PILが利用できない場合は再試行
            pil_available = ensure_pil_available()
            
            # それでも利用できない場合はデフォルト画像を使用
            if not pil_available:
                if debug:
                    print("PILが利用できないため、デフォルトのスペースシャトルを使用します")
                return ImageLoader.load_space_shuttle(bank, x, y), False
        
        try:
            # PILでイメージを開く
            from PIL import Image, ImageEnhance
            
            img = Image.open(img_path)
            
            # 画像の鮮明さを上げる（羽などの細部が見やすくなる）
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.5)  # シャープネスを1.5倍に
            
            # コントラストも少し上げる
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.2)  # コントラストを1.2倍に
            
            # サイズチェック
            width, height = img.size
            if width > 64 or height > 64:
                if debug:
                    print(f"警告: 画像サイズが大きすぎます ({width}x{height}). 64x64以下を推奨します。")
                # アスペクト比を維持してリサイズ
                ratio = min(64 / width, 64 / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                
                # リサイズするときは高品質なLANCZOSフィルタを使用
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
                    
                    # 透明度処理（より細かく）- 羽の表示を改善するために透明度閾値を下げる
                    if a < 30:  # 閾値を50から30に下げて、薄い部分も表示
                        color = 0
                        transparent_pixels += 1
                    else:
                        # 半透明の場合は色を暗くするが、完全に透明にはしない
                        if 30 <= a < 180:
                            factor = a / 255.0
                            r = int(r * factor)
                            g = int(g * factor)
                            b = int(b * factor)
                        
                        # コントラストを強調して視認性を向上
                        r, g, b = ImageLoader.enhance_contrast(r, g, b)
                        
                        # 最も近い色を見つける（改良版アルゴリズム使用）
                        color = ImageLoader.get_closest_color_index(r, g, b)
                        colored_pixels += 1
                    
                    # Pyxelのイメージバンクにピクセルをセット
                    pyxel.images[bank].pset(x + px, y + py, color)
            
            if debug:
                print(f"Pyxelリソースに変換: 透明ピクセル={transparent_pixels}, 色付きピクセル={colored_pixels}")
                # 変換結果をデバッグ用に保存（オプション）
                ImageLoader.debug_save_pixel_map(bank, x, y, width, height)
            
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
        @returns {tuple} - ((height, width), success)形式のタプル
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
            "00755777775557000",
            "00785787878570000",
            "00788787878870000",
            "07888787878887000",
            "07888787878887000",
            "07888888888887000",
            "07888888888887000",
            "07888888888887000",
            "07788585858877000",
            "00775555555577000",
            "00070000000070000",
            "00070000000070000",
            "00077777777770000"
        ]
        
        # イメージバンクにピクセルをセット
        height = len(shuttle_pixels)
        width = len(shuttle_pixels[0])
        
        # イメージバンクをクリア（重要）
        for clear_y in range(height * 2):  # 2フレーム分の領域をクリア
            for clear_x in range(width):
                pyxel.images[bank].pset(x + clear_x, y + clear_y, 0)
        
        # 1枚目のフレームを描画
        for py in range(height):
            for px in range(width):
                color_char = shuttle_pixels[py][px]
                # 文字から色コードに変換
                color = int(color_char) if color_char.isdigit() else 0
                pyxel.images[bank].pset(x + px, y + py, color)
        
        # 2枚目のフレームにコピー（アニメーション用）
        for py in range(height):
            for px in range(width):
                color = pyxel.images[bank].pget(x + px, y + py)
                pyxel.images[bank].pset(x + px, y + height + py, color)
        
        # エンジン炎を追加（両方のフレームに）
        # 1枚目のエンジン炎
        engine_width = width // 3
        engine_center = width // 2
        engine_start = engine_center - engine_width // 2
        engine_end = engine_start + engine_width
        
        # 1枚目のエンジン炎（小さめ）
        for px in range(engine_start, engine_end):
            dist = abs(px - engine_center)
            if dist < engine_width // 4:
                pyxel.images[bank].pset(x + px, y + height - 1, 10)  # 黄色（中央）
            else:
                pyxel.images[bank].pset(x + px, y + height - 1, 9)   # オレンジ（周辺）
        
        # 2枚目のエンジン炎（大きめ）
        for px in range(engine_start, engine_end):
            dist = abs(px - engine_center)
            flame_height = 3 if dist < engine_width // 4 else 2
            
            for flame_y in range(flame_height):
                color = 10 if dist < engine_width // 4 else 9
                pyxel.images[bank].pset(x + px, y + height * 2 - flame_y - 1, color)
        
        # 成功フラグを返す（常に成功）
        return (height, width), True
    
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