"""
リソースローダーモジュール

ゲームで使用する画像や音声などのリソースを読み込む機能を提供します。
"""

import pyxel
import os
import shutil
from utils.pixel_art import PixelArt
from utils.image_loader import ImageLoader, DEBUG

def load_resources():
    """
    ゲームで使用するリソースを読み込みます。
    
    この関数はゲーム開始時に一度だけ呼び出されます。
    """
    if DEBUG:
        print("リソースの読み込みを開始します...")
    
    # リソースディレクトリの存在チェックと作成
    resources_dir = "resources"
    if not os.path.exists(resources_dir):
        if DEBUG:
            print(f"リソースディレクトリが存在しないため作成します: {resources_dir}")
        os.makedirs(resources_dir)
    
    # リソースファイルの存在チェック
    resources_path = os.path.join(resources_dir, "game_resources.pyxres")
    
    if os.path.exists(resources_path):
        # リソースファイルが存在する場合はロード
        if DEBUG:
            print(f"既存のリソースファイルを読み込みます: {resources_path}")
        pyxel.load(resources_path)
        
        # リソースが正しく読み込まれたか検証
        if not ImageLoader.verify_resources(0):
            if DEBUG:
                print("リソースの検証に失敗しました。デフォルトのリソースを作成します。")
            create_default_resources()
    else:
        # リソースファイルがない場合は初期化してデフォルトのリソースを作成
        if DEBUG:
            print("リソースファイルが見つからないため、デフォルトリソースを作成します。")
        create_default_resources()
    
    if DEBUG:
        print("リソースの読み込みが完了しました。")

def create_default_resources():
    """
    デフォルトのゲームリソースを作成します。
    
    リソースファイルが存在しない場合に呼び出され、基本的なグラフィックスを初期化します。
    """
    if DEBUG:
        print("デフォルトリソースの作成を開始します...")
    
    # リソースディレクトリの確認と作成
    resources_dir = "resources"
    if not os.path.exists(resources_dir):
        if DEBUG:
            print(f"リソースディレクトリを作成します: {resources_dir}")
        os.makedirs(resources_dir)
    
    # プレイヤー画像の検証
    player_img_path = os.path.join(resources_dir, "player.png")
    if os.path.exists(player_img_path):
        if DEBUG:
            print(f"プレイヤー画像が見つかりました: {player_img_path}")
        
        # PIL を使って直接画像を読み込んでサイズを取得
        try:
            from PIL import Image
            img = Image.open(player_img_path)
            width, height = img.size
            if DEBUG:
                print(f"PIL から画像情報を取得: サイズ={width}x{height}, モード={img.mode}")
        except Exception as e:
            if DEBUG:
                print(f"PIL 画像読み込みエラー: {e}")
    else:
        if DEBUG:
            print(f"プレイヤー画像が見つかりません: {player_img_path}")
    
    # イメージバンク0：プレイヤーとオプション
    # イメージバンクをクリア
    for y in range(256):
        for x in range(256):
            pyxel.images[0].pset(x, y, 0)
    
    # プレイヤー画像の読み込み
    if DEBUG:
        print("プレイヤー画像を読み込み中...")
    
    # 必ずPILから直接読み込む（サイズの問題を解決するため）
    if os.path.exists(player_img_path):
        try:
            # PIL を使って直接画像を読み込んでリサイズ
            from PIL import Image
            img = Image.open(player_img_path)
            
            # リサイズが必要かチェック
            width, height = img.size
            if width > 64 or height > 64:
                if DEBUG:
                    print(f"画像サイズが大きいのでリサイズします: {width}x{height} → 64x64以下")
                
                # アスペクト比を維持してリサイズ
                ratio = min(64 / width, 64 / height)
                new_width = max(16, int(width * ratio))  # 最小サイズを16に制限
                new_height = max(16, int(height * ratio))
                
                img = img.resize((new_width, new_height), Image.LANCZOS)
                if DEBUG:
                    print(f"リサイズ後のサイズ: {new_width}x{new_height}")
                
                # 処理しやすいようにRGBAに変換
                if img.mode != 'RGBA':
                    if DEBUG:
                        print(f"画像モードを{img.mode}からRGBAに変換します")
                    img = img.convert('RGBA')
                
                # 画像データをPyxelイメージバンクに直接設定
                # 1枚目のフレーム
                for y in range(new_height):
                    for x in range(new_width):
                        r, g, b, a = img.getpixel((x, y))
                        
                        # 透明度判定（細かく）
                        if a < 50:  # ほぼ透明
                            color = 0
                        else:
                            # 半透明の場合は色を暗くする
                            if 50 <= a < 200:
                                factor = a / 255.0
                                r = int(r * factor)
                                g = int(g * factor)
                                b = int(b * factor)
                            
                            # 最も近い色を選択（シンプルな実装）
                            # 白や明るい色
                            if r > 200 and g > 200 and b > 200:
                                color = 7  # 白
                            # 青系
                            elif b > max(r, g) + 50:
                                color = 1 if b < 150 else 12  # 濃い青 or 水色
                            # 赤系
                            elif r > max(g, b) + 50:
                                color = 8  # 赤
                            # 緑系
                            elif g > max(r, b) + 50:
                                color = 11  # 緑
                            # 黄色系
                            elif r > 150 and g > 150 and b < 100:
                                color = 10  # 黄色
                            # グレー系
                            elif abs(r - g) < 30 and abs(g - b) < 30 and abs(b - r) < 30:
                                if r < 100:
                                    color = 5  # 暗いグレー
                                else:
                                    color = 6  # 明るいグレー
                            else:
                                # その他はグレースケールで近似
                                brightness = (r + g + b) // 3
                                if brightness < 80:
                                    color = 0  # 黒
                                elif brightness < 150:
                                    color = 5  # 暗いグレー
                                else:
                                    color = 6  # 明るいグレー
                        
                        # イメージバンクにピクセルを設定
                        pyxel.images[0].pset(x, y, color)
                
                # 2枚目のフレームにコピー（アニメーション用）
                for y in range(new_height):
                    for x in range(new_width):
                        color = pyxel.images[0].pget(x, y)
                        pyxel.images[0].pset(x, y + new_height, color)
                
                # エンジン炎を追加（両方のフレームに）
                # 1枚目
                engine_width = max(4, new_width // 3)
                engine_center = new_width // 2
                engine_start = engine_center - engine_width // 2
                engine_end = engine_start + engine_width
                
                # 1枚目のエンジン炎（小さめ）
                for x in range(engine_start, engine_end):
                    dist = abs(x - engine_center)
                    if dist < engine_width // 4:
                        pyxel.images[0].pset(x, new_height - 1, 10)  # 黄色（中央）
                    else:
                        pyxel.images[0].pset(x, new_height - 1, 9)   # オレンジ（周辺）
                
                # 2枚目のエンジン炎（大きめ）
                for x in range(engine_start, engine_end):
                    dist = abs(x - engine_center)
                    flame_height = 3 if dist < engine_width // 4 else 2
                    
                    for flame_y in range(flame_height):
                        color = 10 if dist < engine_width // 4 else 9
                        pyxel.images[0].pset(x, new_height * 2 - flame_y - 1, color)
                
                # プレイヤー画像のサイズを保存（entity/player.py用）
                player_height, player_width = new_height, new_width
                
                if DEBUG:
                    # 読み込み結果の検証
                    non_transparent = 0
                    for y in range(new_height):
                        for x in range(new_width):
                            if pyxel.images[0].pget(x, y) != 0:
                                non_transparent += 1
                    
                    print(f"画像読み込み完了: サイズ={new_width}x{new_height}, 非透明ピクセル={non_transparent}")
            else:
                # スペースシャトルをデフォルトで使用
                (player_height, player_width), _ = ImageLoader.load_space_shuttle(0, 0, 0)
        except Exception as e:
            if DEBUG:
                print(f"PIL処理中にエラーが発生しました: {e}")
                import traceback
                traceback.print_exc()
            # エラー時はデフォルトのスペースシャトルを使用
            (player_height, player_width), _ = ImageLoader.load_space_shuttle(0, 0, 0)
    else:
        # player.pngがない場合はスペースシャトルを使用
        (player_height, player_width), success = ImageLoader.load_player_png(0, 0, 0)
        
        if not success and DEBUG:
            print("プレイヤー画像の読み込みに失敗したため、デフォルトのスペースシャトルを使用します。")
    
    # ターゲットマーク（プレイヤー識別用）は表示しないように空のスプライトに設定
    if DEBUG:
        print("ターゲットマークの初期化...")
    
    # 空のスプライトを作成
    for y in range(16):
        for x in range(16):
            pyxel.images[0].pset(x + 16, y, 0)
    
    # プレイヤーの弾を設定
    if DEBUG:
        print("弾のリソースを設定...")
    bullet_height, bullet_width = ImageLoader.load_bullet(0, 32, 0)
    
    # オプション（サブウェポン）の設定
    if DEBUG:
        print("オプションのリソースを設定...")
    option_height, option_width = ImageLoader.load_option(0, 8, 0)
    
    # イメージバンク1：ボスとエネミー
    if DEBUG:
        print("ボスのリソースを設定...")
    
    # ドラゴンボス（簡易的な形状）
    pyxel.images[1].set(0, 0, [
        "00000000000000000000000000000000",
        "00001111111111111111111111000000",
        "00011111111111111111111111100000",
        "00111111111111111111111111110000",
        "01111111111111111111111111111000",
        "11111111111111111111111111111100",
        "11110000001111111111000000111100",
        "11100000000111111110000000011100",
        "11100000000011111100000000011100",
        "11100001100001111000011000011100",
        "11100001100000110000011000011100",
        "11110000000000000000000000111100",
        "01111000000000000000000001111000",
        "00111100000000000000000011110000",
        "00011110000001111000000111100000",
        "00001111000011111100001111000000",
        "00000111100111111110011110000000",
        "00000011111111111111111100000000",
        "00000001111111111111111000000000",
        "00000000111111111111100000000000",
        "00000000011111111111000000000000",
        "00000000001111111110000000000000",
        "00000000000111111110000000000000",
        "00000000001111111111000000000000",
        "00000000011111111111100000000000",
        "00000000111111111111110000000000",
        "00000001111110001111110000000000",
        "00000011111100000111111000000000",
        "00000111111000000011111100000000",
        "00001111110000000001111110000000",
        "00011111100000000000111111000000",
        "00111111000000000000011111100000"
    ])
    
    # イメージバンク2：パワーアップアイテムと障害物
    if DEBUG:
        print("パワーアップアイテムのリソースを設定...")
    
    # パワーアップP
    pyxel.images[2].set(0, 0, [
        "00111100",
        "01111110",
        "11111111",
        "11100111",
        "11100111",
        "11111110",
        "11111100",
        "11100000"
    ])
    
    # 残機アップL
    pyxel.images[2].set(8, 0, [
        "01100000",
        "01100000",
        "01100000",
        "01100000",
        "01100000",
        "01100000",
        "01111110",
        "01111110"
    ])
    
    # ボムアップB
    pyxel.images[2].set(16, 0, [
        "11111100",
        "11111110",
        "11000111",
        "11111110",
        "11111110",
        "11000111",
        "11111110",
        "11111100"
    ])
    
    # 音楽とSEの初期化
    if DEBUG:
        print("サウンドリソースを初期化...")
    init_sounds()
    
    # 作成したリソースを保存
    if DEBUG:
        print("作成したリソースを保存します...")
    save_resources()
    
    # 最終検証
    if DEBUG:
        print("リソースの最終検証を行います...")
        result = ImageLoader.verify_resources(0)
        print(f"リソース検証結果: {'成功' if result else '失敗'}")
    
    if DEBUG:
        print("デフォルトリソースの作成が完了しました。")

def init_sounds():
    """
    ゲームで使用する音楽と効果音を初期化します。
    """
    if DEBUG:
        print("サウンドの初期化を行います...")
    
    # 効果音0: ショット音
    sound0 = pyxel.Sound()
    sound0.set("c3e3g3c4c4", "s", "4", "n", 7)
    pyxel.sounds[0] = sound0
    
    # 効果音1: 爆発音
    sound1 = pyxel.Sound()
    sound1.set("f2c2f1c1f1", "n", "5", "f", 8)
    pyxel.sounds[1] = sound1
    
    # 効果音2: パワーアップ取得音
    sound2 = pyxel.Sound()
    sound2.set("c3e3g3c4", "t", "5", "n", 5)
    pyxel.sounds[2] = sound2
    
    # 効果音3: ボム使用音
    sound3 = pyxel.Sound()
    sound3.set("f1c2f2c3f3", "t", "6", "f", 3)
    pyxel.sounds[3] = sound3
    
    # 効果音4: プレイヤー被弾音
    sound4 = pyxel.Sound()
    sound4.set("c2", "p", "6", "n", 1)
    pyxel.sounds[4] = sound4

def save_resources():
    """
    作成したリソースをファイルに保存します。
    """
    # resources ディレクトリがない場合は作成
    resources_dir = "resources"
    if not os.path.exists(resources_dir):
        if DEBUG:
            print(f"保存用のリソースディレクトリを作成します: {resources_dir}")
        os.makedirs(resources_dir)
    
    resources_path = os.path.join(resources_dir, "game_resources.pyxres")
    
    # 既存のリソースファイルがある場合はバックアップ
    if os.path.exists(resources_path):
        backup_path = resources_path + ".bak"
        if DEBUG:
            print(f"既存のリソースファイルをバックアップします: {backup_path}")
        try:
            shutil.copy2(resources_path, backup_path)
        except Exception as e:
            if DEBUG:
                print(f"バックアップ作成中にエラーが発生しました: {e}")
    
    # リソースを保存
    if DEBUG:
        print(f"リソースを保存します: {resources_path}")
    pyxel.save(resources_path)

def play_sound(sound_id):
    """
    指定したIDの効果音を再生します。
    
    @param {number} sound_id - 再生する効果音のID
    """
    pyxel.play(0, sound_id) 