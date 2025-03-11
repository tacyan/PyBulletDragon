"""
リソースローダーモジュール

ゲームで使用する画像や音声などのリソースを読み込む機能を提供します。
"""

import pyxel
import os
import sys
import shutil
from utils.pixel_art import PixelArt
from utils.image_loader import ImageLoader, DEBUG, ensure_pil_available

def load_resources():
    """
    ゲームで使用するリソースを読み込みます。
    
    この関数はゲーム開始時に一度だけ呼び出されます。
    """
    if DEBUG:
        print("リソースの読み込みを開始します...")
    
    # Pyodide環境でPILが利用可能か確認
    pil_available = ensure_pil_available()
    if pil_available and DEBUG:
        print("PIL/Pillowが利用可能です")
    
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
    
    # PILの利用可能性を確認
    pil_available = ensure_pil_available()
    
    # リソースディレクトリの確認と作成
    resources_dir = "resources"
    if not os.path.exists(resources_dir):
        if DEBUG:
            print(f"リソースディレクトリを作成します: {resources_dir}")
        os.makedirs(resources_dir)
    
    # イメージバンク0：プレイヤーとオプション
    # イメージバンクをクリア
    for y in range(256):
        for x in range(256):
            pyxel.images[0].pset(x, y, 0)
    
    # プレイヤー画像の読み込み
    if DEBUG:
        print("プレイヤー画像を読み込み中...")
    
    # プレイヤー画像情報の初期設定
    player_dimensions = (0, 0)  # 高さ、幅
    loading_success = False
    
    # プレイヤー画像処理 - 直接ImageLoaderを使用して確実に読み込み
    try:
        # 画像ファイルが存在し、PILが利用可能な場合は高品質処理
        player_img_path = os.path.join(resources_dir, "player.png")
        
        if DEBUG:
            print(f"プレイヤー画像のパス: {os.path.abspath(player_img_path)}")
            print(f"ファイルの存在: {os.path.exists(player_img_path)}")
            print(f"PILの利用可能性: {pil_available}")
        
        # ImageLoaderを使った確実な読み込み
        result_tuple, success = ImageLoader.load_player_png(0, 0, 0)
        player_dimensions = result_tuple
        loading_success = success
        
        if DEBUG:
            print(f"プレイヤー画像の読み込み結果: サイズ={player_dimensions}, 成功={loading_success}")
            
        if not success:
            if DEBUG:
                print("プレイヤー画像の読み込みに失敗しました。デフォルトのスペースシャトルを使用します。")
            # エラー時はデフォルトのスペースシャトルを使用
            result_tuple, _ = ImageLoader.load_space_shuttle(0, 0, 0)
            player_dimensions = result_tuple
    except Exception as e:
        if DEBUG:
            print(f"プレイヤー画像処理中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
        
        # エラー時はデフォルトのスペースシャトルを使用
        result_tuple, _ = ImageLoader.load_space_shuttle(0, 0, 0)
        player_dimensions = result_tuple
    
    player_height, player_width = player_dimensions
    
    if DEBUG:
        print(f"プレイヤー画像の最終サイズ: {player_width}x{player_height}")
        
    # 確実に画像が読み込まれたか確認（デバッグ用）
    if DEBUG:
        non_transparent_pixels = 0
        for y in range(player_height):
            for x in range(player_width):
                if pyxel.images[0].pget(x, y) != 0:
                    non_transparent_pixels += 1
        print(f"プレイヤー画像の非透明ピクセル数: {non_transparent_pixels}")
    
    # ターゲットマーク（プレイヤー識別用）
    if DEBUG:
        print("ターゲットマークの初期化...")
    
    # 空のスプライトを作成
    for y in range(16):
        for x in range(16):
            pyxel.images[0].pset(x + 16, y, 0)
    
    # プレイヤーの弾を設定
    if DEBUG:
        print("プレイヤーの弾のリソースを設定...")
    
    # 弾の設定 - より確実に
    bullet_result, bullet_success = ImageLoader.load_bullet(0, 32, 0)
    bullet_height, bullet_width = bullet_result
    
    if DEBUG:
        print(f"プレイヤー弾のリソース設定結果: サイズ={bullet_width}x{bullet_height}, 成功={bullet_success}")
        
        # 弾が正しく設定されたか確認
        bullet_non_transparent = 0
        for cy in range(bullet_height):
            for cx in range(bullet_width):
                if pyxel.images[0].pget(32 + cx, 0 + cy) != 0:
                    bullet_non_transparent += 1
        print(f"プレイヤー弾の非透明ピクセル数: {bullet_non_transparent}")
    
    # オプション（サブウェポン）を設定
    if DEBUG:
        print("オプションのリソースを設定...")
    option_dimensions, _ = ImageLoader.load_option(0, 40, 0)
    
    # イメージバンク1：敵と障害物
    # イメージバンクをクリア
    for y in range(256):
        for x in range(256):
            pyxel.images[1].pset(x, y, 0)
    
    # 敵キャラの設定
    if DEBUG:
        print("敵キャラのリソースを設定...")
    PixelArt.create_enemy_small(1, 0, 0)
    PixelArt.create_enemy_medium(1, 16, 0)
    PixelArt.create_enemy_large(1, 32, 0)
    PixelArt.create_boss_phase1(1, 64, 0)
    PixelArt.create_boss_phase2(1, 64, 32)
    PixelArt.create_boss_phase3(1, 64, 64)
    
    # 障害物の設定
    if DEBUG:
        print("障害物のリソースを設定...")
    PixelArt.create_asteroid_small(1, 48, 0)
    PixelArt.create_asteroid_medium(1, 56, 0)
    PixelArt.create_asteroid_large(1, 0, 32)
    
    # イメージバンク2：弾とエフェクト
    # イメージバンクをクリア
    for y in range(256):
        for x in range(256):
            pyxel.images[2].pset(x, y, 0)
    
    # 弾の設定
    if DEBUG:
        print("一般的な弾のリソースを設定...")
    PixelArt.create_bullet_small(2, 0, 0)
    PixelArt.create_bullet_medium(2, 8, 0)
    PixelArt.create_bullet_large(2, 16, 0)
    
    # エフェクトの設定
    if DEBUG:
        print("エフェクトのリソースを設定...")
    PixelArt.create_explosion_small(2, 0, 16)
    PixelArt.create_explosion_medium(2, 16, 16)
    PixelArt.create_explosion_large(2, 32, 16)
    
    # アイテムの設定
    if DEBUG:
        print("アイテムのリソースを設定...")
    PixelArt.create_power_up(2, 64, 0)
    PixelArt.create_life_up(2, 72, 0)
    PixelArt.create_bomb_item(2, 80, 0)
    
    # サウンド効果の設定
    if DEBUG:
        print("サウンドリソースを設定...")
    init_sounds()
    
    # リソースの保存
    save_resources()
    
    if DEBUG:
        print("デフォルトリソースの作成が完了しました。")

def init_sounds():
    """
    サウンド効果を初期化します。
    """
    # チャンネル0: プレイヤーの弾発射音
    pyxel.sounds[0].set(
        "a3a2c1a1",  # ノート
        "p",         # トーン
        "7",         # ボリューム
        "s",         # エフェクト
        20           # 速度
    )
    
    # チャンネル1: 爆発音
    pyxel.sounds[1].set(
        "f2d2b1g1",  # ノート
        "n",         # トーン
        "7",         # ボリューム
        "s",         # エフェクト
        10           # 速度
    )
    
    # チャンネル2: パワーアップ音
    pyxel.sounds[2].set(
        "c3e3g3c4",  # ノート
        "s",         # トーン
        "7",         # ボリューム
        "n",         # エフェクト
        20           # 速度
    )
    
    # チャンネル3: ダメージ音
    pyxel.sounds[3].set(
        "d2a1e1c1",  # ノート
        "n",         # トーン
        "7",         # ボリューム
        "s",         # エフェクト
        10           # 速度
    )
    
    # ミュージック0: タイトル画面用BGM
    pyxel.musics[0].set([], [], [], [])
    
    # ミュージック1: ゲームプレイ中のBGM
    pyxel.musics[1].set([], [], [], [])

def save_resources():
    """
    作成したリソースを保存します。
    """
    try:
        resources_dir = "resources"
        if not os.path.exists(resources_dir):
            os.makedirs(resources_dir)
        
        resources_path = os.path.join(resources_dir, "game_resources.pyxres")
        pyxel.save(resources_path)
        
        if DEBUG:
            print(f"リソースを保存しました: {resources_path}")
    except Exception as e:
        if DEBUG:
            print(f"リソース保存中にエラーが発生しました: {e}")

def play_sound(sound_id):
    """
    サウンドを再生します。
    
    @param {number} sound_id - 再生するサウンドのID
    """
    try:
        pyxel.play(0, sound_id)
    except Exception as e:
        if DEBUG:
            print(f"サウンド再生中にエラーが発生しました: {e}") 