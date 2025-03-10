"""
デバッグスクリプト

player.png画像の読み込みと表示をテストするためのスクリプトです。
画像が正しく読み込まれているかを確認するために使用します。
"""

import pyxel
import os
from PIL import Image
import sys
import math

# デバッグモード
DEBUG = True

class DebugApp:
    """
    player.png画像の読み込みと表示をテストするアプリケーションクラス
    """
    def __init__(self):
        # Pyxelの初期化
        pyxel.init(160, 120, title="Player Image Test")
        
        # resourcesフォルダの確認
        self.resources_dir = "resources"
        if not os.path.exists(self.resources_dir):
            print(f"リソースディレクトリが存在しないため作成します: {self.resources_dir}")
            os.makedirs(self.resources_dir)
        
        # 画像パスのチェック
        self.player_img_path = os.path.join(self.resources_dir, "player.png")
        self.has_player_image = os.path.exists(self.player_img_path)
        
        if self.has_player_image:
            print(f"player.png画像が見つかりました: {self.player_img_path}")
            # PIL画像として読み込んでサイズを取得
            try:
                self.pil_img = Image.open(self.player_img_path)
                self.pil_width, self.pil_height = self.pil_img.size
                self.pil_mode = self.pil_img.mode
                print(f"画像情報: サイズ={self.pil_width}x{self.pil_height}, モード={self.pil_mode}")
                
                # 画像が大きすぎる場合は警告
                if self.pil_width > 64 or self.pil_height > 64:
                    print(f"警告: 画像サイズが大きすぎます。64x64以下を推奨します。")
                    print(f"      自動的にリサイズされます。")
                    ratio = min(64 / self.pil_width, 64 / self.pil_height)
                    self.scaled_width = int(self.pil_width * ratio)
                    self.scaled_height = int(self.pil_height * ratio)
                    print(f"      リサイズ後のサイズ: {self.scaled_width}x{self.scaled_height}")
                else:
                    self.scaled_width = self.pil_width
                    self.scaled_height = self.pil_height
            except Exception as e:
                print(f"PIL読み込みエラー: {e}")
                self.pil_img = None
        else:
            print(f"player.png画像が見つかりません: {self.player_img_path}")
            self.pil_img = None
        
        # Pyxelリソースの初期化
        self.init_resources()
        
        # 実行
        pyxel.run(self.update, self.draw)
    
    def init_resources(self):
        """
        リソースを初期化し、player.png画像を読み込みます。
        """
        # イメージバンクのクリア
        for y in range(256):
            for x in range(256):
                pyxel.images[0].pset(x, y, 0)
        
        # player.pngがあれば読み込み
        if self.has_player_image and self.pil_img:
            try:
                print("Pyxelにplayer.png画像を読み込みます...")
                img_data = self.convert_image_to_pyxel_format()
                
                # イメージバンクに画像データをセット
                width = min(64, self.pil_width)
                height = min(64, self.pil_height)
                
                # 画像をPyxelのイメージバンクにセット
                for y in range(height):
                    for x in range(width):
                        if y < len(img_data) and x < len(img_data[y]):
                            pyxel.images[0].pset(x, y, img_data[y][x])
                
                # 2枚目のフレームをコピー（アニメーション用）
                for y in range(height):
                    for x in range(width):
                        if y < len(img_data) and x < len(img_data[y]):
                            pyxel.images[0].pset(x, y + height, img_data[y][x])
                
                # エンジン炎を追加
                engine_width = width // 3
                engine_start_x = (width - engine_width) // 2
                engine_end_x = engine_start_x + engine_width
                
                # 1枚目のエンジン炎（小さめ）
                engine_y1 = height - 1  # 1枚目の画像の下部
                for x in range(engine_start_x, engine_end_x):
                    # 中央に近いほど長い炎に
                    distance_from_center = abs(x - (engine_start_x + engine_width//2))
                    if distance_from_center < engine_width // 4:
                        pyxel.images[0].pset(x, engine_y1, 10)  # 黄色（中央）
                    elif distance_from_center < engine_width // 2:
                        pyxel.images[0].pset(x, engine_y1, 9)   # オレンジ（周辺）
                
                # 2枚目のエンジン炎（長め）
                engine_y2 = height * 2 - 1  # 2枚目の画像の下部
                for x in range(engine_start_x, engine_end_x):
                    # 中央に近いほど長い炎に
                    distance_from_center = abs(x - (engine_start_x + engine_width//2))
                    flame_length = max(1, 3 - distance_from_center // 2)
                    
                    for flame_y in range(flame_length):
                        flame_color = 10 if distance_from_center < engine_width // 4 else 9
                        pyxel.images[0].pset(x, engine_y2 - flame_y, flame_color)
                
                print(f"画像読み込み完了: {width}x{height}")
                
                # リソースの検証
                self.verify_resources()
                
            except Exception as e:
                print(f"Pyxel読み込みエラー: {e}")
                import traceback
                traceback.print_exc()
        
        # デフォルトのスプライトを作成（読み込み失敗時のフォールバック）
        self.create_default_sprite()
    
    def verify_resources(self):
        """
        リソースの内容を検証します。
        """
        print("リソース検証:")
        
        # 1枚目のフレームの非透明ピクセルをカウント
        non_transparent_1 = 0
        for y in range(64):
            for x in range(64):
                if pyxel.images[0].pget(x, y) != 0:
                    non_transparent_1 += 1
        
        # 2枚目のフレームの非透明ピクセルをカウント
        non_transparent_2 = 0
        for y in range(64):
            for x in range(64):
                if pyxel.images[0].pget(x, y + 64) != 0:
                    non_transparent_2 += 1
        
        print(f"  フレーム1の非透明ピクセル: {non_transparent_1}")
        print(f"  フレーム2の非透明ピクセル: {non_transparent_2}")
        
        if non_transparent_1 == 0:
            print("  警告: フレーム1に有効なピクセルがありません！")
        if non_transparent_2 == 0:
            print("  警告: フレーム2に有効なピクセルがありません！")
    
    def convert_image_to_pyxel_format(self):
        """
        PIL画像をPyxel形式に変換します。
        
        @returns {list} - Pyxel形式の画像データ
        """
        if not self.pil_img:
            return []
        
        # PIL画像を適切なサイズにリサイズ
        max_size = 64
        if self.pil_width > max_size or self.pil_height > max_size:
            # アスペクト比を維持しながらリサイズ
            ratio = min(max_size / self.pil_width, max_size / self.pil_height)
            new_width = int(self.pil_width * ratio)
            new_height = int(self.pil_height * ratio)
            
            resized_img = self.pil_img.resize((new_width, new_height), Image.LANCZOS)
            print(f"画像をリサイズしました: {new_width}x{new_height}")
        else:
            resized_img = self.pil_img
        
        # RGBAモードに変換
        if resized_img.mode != 'RGBA':
            if resized_img.mode == 'RGB':
                # RGBからRGBAに変換（透明度は最大に）
                rgba_img = Image.new("RGBA", resized_img.size)
                rgba_img.paste(resized_img, (0, 0))
                resized_img = rgba_img
                print(f"画像モードをRGBからRGBAに変換しました")
            else:
                # その他のモードはRGBAに変換
                resized_img = resized_img.convert('RGBA')
                print(f"画像モードを{self.pil_img.mode}からRGBAに変換しました")
        
        # 画像データをPyxel形式に変換
        width, height = resized_img.size
        img_data = []
        
        # 色変換の統計
        color_counts = [0] * 16
        transparent_count = 0
        
        for y in range(height):
            row = []
            for x in range(width):
                r, g, b, a = resized_img.getpixel((x, y))
                
                # 透明度判定
                if a < 50:  # ほぼ透明
                    color = 0
                    transparent_count += 1
                else:
                    # 最も近いPyxelパレットの色を選択
                    color = self.get_closest_color(r, g, b)
                    color_counts[color] += 1
                
                row.append(color)
            img_data.append(row)
        
        print(f"画像変換統計: 透明={transparent_count}, 非透明={width*height - transparent_count}")
        for i, count in enumerate(color_counts):
            if count > 0:
                print(f"  色{i}: {count}ピクセル")
        
        return img_data
    
    def create_default_sprite(self):
        """
        デフォルトのスプライトを作成します（読み込み失敗時のフォールバック）。
        """
        # 機体のフレーム
        for y in range(8):
            for x in range(8):
                if x == 0 or x == 7 or y == 0 or y == 7:
                    pyxel.images[0].pset(x + 70, y, 7)  # 白の輪郭
                else:
                    pyxel.images[0].pset(x + 70, y, 6)  # 灰色の内部
        
        # エンジン炎
        pyxel.images[0].pset(73, 8, 10)  # 黄色
        pyxel.images[0].pset(74, 8, 10)
        pyxel.images[0].pset(73, 9, 9)   # オレンジ
        pyxel.images[0].pset(74, 9, 9)
    
    def get_closest_color(self, r, g, b):
        """
        RGB値に最も近いPyxelパレットの色のインデックスを返します。
        """
        # Pyxelパレット (RGB値)
        palette = [
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
        
        # 最小距離と色インデックス
        min_distance = float('inf')
        closest_index = 0
        
        # 各パレット色との距離を計算
        for i, color in enumerate(palette):
            distance = math.sqrt(
                (r - color[0]) ** 2 + 
                (g - color[1]) ** 2 + 
                (b - color[2]) ** 2
            )
            if distance < min_distance:
                min_distance = distance
                closest_index = i
        
        return closest_index
    
    def update(self):
        """
        フレーム更新時の処理
        """
        # ESCキーで終了
        if pyxel.btnp(pyxel.KEY_Q) or pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()
        
        # Sキーでスクリーンショットを保存
        if pyxel.btnp(pyxel.KEY_S):
            pyxel.screenshot(os.path.join(self.resources_dir, "debug_screenshot.png"))
            print("スクリーンショットを保存しました: resources/debug_screenshot.png")
        
        # Rキーでリソースを再読み込み
        if pyxel.btnp(pyxel.KEY_R):
            print("リソースを再読み込みします...")
            self.init_resources()
    
    def draw(self):
        """
        描画処理
        """
        # 画面クリア
        pyxel.cls(0)
        
        # タイトル
        pyxel.text(5, 5, "Player Image Test", 7)
        
        # 読み込み状態
        status_text = "Found" if self.has_player_image else "Not Found"
        status_color = 11 if self.has_player_image else 8
        pyxel.text(5, 15, f"player.png: {status_text}", status_color)
        
        # PIL情報
        if self.pil_img:
            pyxel.text(5, 25, f"Size: {self.pil_width}x{self.pil_height}", 7)
            pyxel.text(5, 35, f"Mode: {self.pil_mode}", 7)
        
        # アニメーション情報
        frame = (pyxel.frame_count // 8) % 2
        y_offset = 0 if frame == 0 else min(64, self.scaled_height) if hasattr(self, 'scaled_height') else 64
        pyxel.text(5, 45, f"Frame: {frame}, Y-offset: {y_offset}", 7)
        
        # 画像の表示（バンク0から）
        if self.has_player_image and self.pil_img:
            # フレーム1（静止画像）
            pyxel.text(5, 60, "Frame 1:", 7)
            width = min(64, self.scaled_width) if hasattr(self, 'scaled_width') else min(64, self.pil_width)
            height = min(32, self.scaled_height) if hasattr(self, 'scaled_height') else min(32, self.pil_height)
            pyxel.blt(40, 60, 0, 0, 0, width, height, 0)
            
            # フレーム2（アニメーション）
            pyxel.text(5, 95, "Frame 2:", 7)
            pyxel.blt(40, 95, 0, 0, height, width, height, 0)
            
            # バウンディングボックスを表示（見やすさのため）
            pyxel.rectb(40, 60, width, height, 5)
            pyxel.rectb(40, 95, width, height, 5)
        else:
            # デフォルトスプライト
            pyxel.text(5, 60, "Default Sprite:", 7)
            pyxel.blt(40, 60, 0, 70, 0, 8, 10, 0)
            
            # バウンディングボックスを表示
            pyxel.rectb(40, 60, 8, 10, 5)
        
        # 操作説明
        pyxel.text(5, 110, "Q:Quit R:Reload S:Screenshot", 13)

# メイン実行
if __name__ == "__main__":
    print("player.png画像テストを開始します...")
    print(f"カレントディレクトリ: {os.getcwd()}")
    
    try:
        app = DebugApp()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc() 