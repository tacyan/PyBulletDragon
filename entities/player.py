"""
プレイヤークラスモジュール

プレイヤーキャラクターの動作、描画、状態管理を担当するクラスを定義します。
"""

import pyxel
import math
import time
import os
import sys
from utils.image_loader import DEBUG, ensure_pil_available

# プレイヤー関連の定数
PLAYER_SPEED = 5  # プレイヤーの移動速度（3から5に増加）
PLAYER_BULLET_SPEED = 6  # プレイヤーの弾の速度
MAX_POWER_LEVEL = 5  # 最大パワーレベル
INVINCIBLE_TIME = 60  # 無敵時間（フレーム数）
HITBOX_RADIUS = 2  # 当たり判定の半径
DOUBLE_TAP_TIME = 0.3  # ダブルタップの時間閾値（秒）
CONTROL_AREA_HEIGHT = 200  # 操作領域の高さ（画面下部から）
JOYSTICK_MAX_SPEED_FACTOR = 1.8  # ジョイスティック最大速度倍率（2.5から1.8に減少）
JOYSTICK_SENSITIVITY = 25  # ジョイスティック感度（小さいほど敏感）

# PILエラー時のフォールバックのためのフラグ
FALLBACK_ON_PIL_ERROR = True

class Bullet:
    """
    プレイヤーの弾クラス
    
    プレイヤーが発射する弾の動作や描画を管理します。
    """
    def __init__(self, x, y, angle=math.pi/2, speed=PLAYER_BULLET_SPEED, power=1):
        """
        弾を初期化します。
        
        @param {number} x - 弾のX座標
        @param {number} y - 弾のY座標
        @param {number} angle - 弾の進行方向（ラジアン、デフォルトは上方向）
        @param {number} speed - 弾の速度
        @param {number} power - 弾の威力
        """
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = -math.sin(angle) * speed  # 画面座標系では上がマイナス方向
        self.width = 5  # ビームの幅（5ピクセル）
        self.height = 6  # ビームの高さ（6ピクセル）
        self.power = power
        self.is_active = True
        self.animation_frame = 0  # アニメーションフレーム
    
    def update(self):
        """
        弾の状態を更新します。
        
        @returns {boolean} - 弾が画面外に出たらTrue
        """
        self.x += self.vx
        self.y += self.vy
        
        # アニメーションフレームの更新
        self.animation_frame = (self.animation_frame + 1) % 4
        
        # 画面外に出たら削除フラグを立てる
        if (self.x < -self.width or self.x > pyxel.width + self.width or
            self.y < -self.height or self.y > pyxel.height + self.height):
            return True
        return False
    
    def draw(self):
        """
        弾を描画します。
        """
        # 弾のスプライトを描画 - 座標をより正確に調整
        pyxel.blt(
            int(self.x - 2.5),  # 中心に配置するため調整
            int(self.y - 3),    # 位置調整
            0,                  # イメージバンク
            32, 0,              # 弾スプライトの位置
            5, 6,               # 弾の幅と高さ
            0                   # 透明色
        )
        
        # 発射エフェクト（見た目を強化）
        if self.animation_frame < 2:
            # 明るいエフェクト（点滅と軌跡）
            pyxel.pset(self.x, self.y + 2, 7)  # 白色の点（中央）
            
            # 速度に応じた軌跡
            trail_length = int(max(1, min(3, math.sqrt(self.vx**2 + self.vy**2) / 2)))
            for i in range(1, trail_length + 1):
                # 進行方向と逆に軌跡を描画
                trail_x = int(self.x - (self.vx * i / 3))
                trail_y = int(self.y - (self.vy * i / 3))
                trail_color = 6 if i == 1 else 5  # 近い部分は明るく
                pyxel.pset(trail_x, trail_y, trail_color)

class Player:
    """
    プレイヤークラス
    
    プレイヤーキャラクターの動作、状態管理、描画を担当します。
    """
    def __init__(self):
        """
        プレイヤーを初期化します。
        """
        # プレイヤー画像サイズの検出
        self._detect_player_image_size()
        
        # プレイヤーの位置設定
        self.x = pyxel.width // 2 - self.width // 2  # 中心に配置するため調整
        self.y = pyxel.height - 40 - self.height     # 少し高めの位置に配置
        
        # ゲームプレイ関連の初期化
        self.bullets = []
        self.power = 1  # プレイヤーのパワーレベル
        self.lives = 3  # 残機数
        self.invincible = 0  # 無敵時間（フレーム数）
        self.hitbox_radius = HITBOX_RADIUS  # 当たり判定の半径
        self.shot_cooldown = 0  # 連射クールダウン
        self.options = []  # オプション（サブウェポン）位置
        self.bomb = 3  # ボム数
        
        # 移動関連
        self.is_focusing = False  # 低速移動（集中モード）フラグ
        self.focus_speed = PLAYER_SPEED / 2  # 低速移動時の速度
        
        # タッチ操作関連
        self.touch_start_x = 0
        self.touch_start_y = 0
        self.touch_start_time = 0
        self.last_tap_time = 0
        self.is_touching = False
        self.touch_control_mode = "direct"  # 操作モード: "direct" または "joystick"
        self.target_x = self.x  # 移動先のX座標
        self.target_y = self.y  # 移動先のY座標
        self.joystick_center_x = 0  # 仮想ジョイスティックの中心X
        self.joystick_center_y = 0  # 仮想ジョイスティックの中心Y
        self.move_smoothness = 0.4  # 移動の滑らかさ（値が大きいほど素早く移動）
        self.joystick_active = False  # ジョイスティックが有効かどうか
        self.joystick_duration = 0  # ジョイスティック操作の持続時間
        
        # 画像アニメーション関連
        self.animation_frame = 0  # アニメーションフレーム
        self.frame_offset = self.height  # 2枚目のフレームのY位置オフセット
        
        if DEBUG:
            print(f"プレイヤー初期化完了: サイズ={self.width}x{self.height}, 位置=({self.x}, {self.y})")
    
    def _detect_player_image_size(self):
        """
        プレイヤー画像のサイズを検出します。
        画像が見つからない場合はデフォルトサイズを使用します。
        """
        try:
            # 方法1: イメージバンク0の内容から直接サイズを検出（最も信頼性が高い方法）
            # 非透明ピクセルがある範囲を計算
            min_x, min_y = 999, 999
            max_x, max_y = 0, 0
            found_pixels = False
            
            # スキャン範囲を広く取る（最大64x64まで）
            scan_max = 64
            
            for y in range(scan_max):
                for x in range(scan_max):
                    # 2フレーム分のアニメーションのうち、1フレーム目だけをスキャン
                    if pyxel.images[0].pget(x, y) != 0:  # 非透明ピクセル
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                        max_x = max(max_x, x)
                        max_y = max(max_y, y)
                        found_pixels = True
            
            if found_pixels:
                # 非透明ピクセルが見つかった
                width = max_x - min_x + 1
                height = max_y - min_y + 1
                
                if DEBUG:
                    print(f"バンク0から検出したサイズ: {width}x{height}, 範囲=({min_x},{min_y})-({max_x},{max_y})")
                
                # サイズの妥当性チェック（異常に小さい場合は除外）
                if width >= 8 and height >= 8:
                    # 画像の場合、高さの2倍まで幅を広げる（羽を含むため）
                    # これにより、羽の部分もきちんと描画される
                    self.width = max(width, min(64, int(height * 1.5)))
                    self.height = height
                    self.frame_offset = height  # 2フレーム目のオフセット
                    
                    if DEBUG:
                        print(f"プレイヤー画像サイズを設定: {self.width}x{self.height}")
                    return
            
            # 方法2: PILを使って画像サイズを直接取得（バックアップ方法）
            img_path = os.path.join("resources", "player.png")
            if os.path.exists(img_path):
                # PILが利用可能かを確認
                pil_available = ensure_pil_available()
                
                if pil_available:
                    try:
                        # PIL動的インポート
                        from PIL import Image
                        img = Image.open(img_path)
                        orig_width, orig_height = img.size
                        
                        # リサイズが必要かチェック
                        if orig_width > 64 or orig_height > 64:
                            ratio = min(64 / orig_width, 64 / orig_height)
                            width = max(16, int(orig_width * ratio))  # 最小サイズを16に制限
                            height = max(16, int(orig_height * ratio))
                        else:
                            width = orig_width
                            height = orig_height
                        
                        if DEBUG:
                            print(f"PIL から直接サイズを取得: 元のサイズ={orig_width}x{orig_height}, 使用サイズ={width}x{height}")
                        
                        # 検出されたサイズを設定
                        self.width = width
                        self.height = height
                        self.frame_offset = height  # 2フレーム目のオフセット
                        
                        return
                    except Exception as e:
                        if DEBUG:
                            print(f"PILを使用した画像サイズの検出中にエラー: {e}")
                else:
                    if DEBUG:
                        print("PILが利用できないため、デフォルトサイズを使用します")
            
            # いずれの方法でも検出できなかった場合はデフォルトサイズを使用
            self.width = 32  # デフォルト幅
            self.height = 32  # デフォルト高さ
            self.frame_offset = self.height
            
            if DEBUG:
                print(f"デフォルトのサイズを使用: {self.width}x{self.height}")
            
        except Exception as e:
            if DEBUG:
                print(f"画像サイズ検出中にエラーが発生しました: {e}")
                import traceback
                traceback.print_exc()
            
            # エラー時はデフォルトサイズを使用
            self.width = 32
            self.height = 32
            self.frame_offset = self.height
            
            if DEBUG:
                print(f"エラー時のデフォルトサイズを使用: {self.width}x{self.height}")
    
    def update(self):
        """
        プレイヤーの状態を更新します。
        """
        # キーボード操作
        self.handle_keyboard_input()
        
        # タッチ操作
        self.handle_touch_input()
        
        # 目標位置への滑らかな移動
        if self.x != self.target_x or self.y != self.target_y:
            # 移動速度の計算（低速移動モードか通常かで分岐）
            move_speed = self.focus_speed if self.is_focusing else PLAYER_SPEED
            
            # 既存のmove_smoothnessプロパティを利用（0.4が初期値）
            easing_factor = self.move_smoothness
            
            # 現在位置と目標位置の差分を計算
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            
            # 距離に応じたスムージング（イージング）
            self.x += dx * easing_factor
            self.y += dy * easing_factor
            
            # ごく小さな差分の場合は位置を合わせる（浮動小数点の誤差防止）
            if abs(dx) < 0.5:
                self.x = self.target_x
            if abs(dy) < 0.5:
                self.y = self.target_y
        
        # ショットクールダウンを減少
        if self.shot_cooldown > 0:
            self.shot_cooldown -= 1
            
        # 連射機能（Zキーを押している間は常に発射）
        if pyxel.btn(pyxel.KEY_Z) and self.shot_cooldown == 0:
            self.shoot()
            self.shot_cooldown = 2  # 連射速度をさらに上げる（3から2に変更）
        
        # 弾の更新
        for bullet in self.bullets[:]:
            if bullet.update():
                self.bullets.remove(bullet)
        
        # オプションの位置更新
        self.update_options()
        
        # 無敵時間の更新
        if self.invincible > 0:
            self.invincible -= 1
    
    def handle_keyboard_input(self):
        """
        キーボード入力を処理します。
        """
        # 低速移動モードの切り替え
        self.is_focusing = pyxel.btn(pyxel.KEY_SHIFT)
        
        # 現在の移動速度を決定
        current_speed = self.focus_speed if self.is_focusing else PLAYER_SPEED
        
        # 移動方向のフラグ
        move_horizontal = False
        move_vertical = False
        dx = 0
        dy = 0
        
        # 水平方向の移動
        if pyxel.btn(pyxel.KEY_LEFT) and self.x > 0:
            dx -= current_speed
            move_horizontal = True
        if pyxel.btn(pyxel.KEY_RIGHT) and self.x < pyxel.width - self.width:
            dx += current_speed
            move_horizontal = True
            
        # 垂直方向の移動
        if pyxel.btn(pyxel.KEY_UP) and self.y > 0:
            dy -= current_speed
            move_vertical = True
        if pyxel.btn(pyxel.KEY_DOWN) and self.y < pyxel.height - self.height:
            dy += current_speed
            move_vertical = True
            
        # 斜め移動時は速度を調整（ノーマライズ）
        if move_horizontal and move_vertical:
            diagonal_factor = 0.8  # 斜め移動時の速度調整係数（0.707より大きめに設定）
            dx *= diagonal_factor
            dy *= diagonal_factor
            
        # 移動を適用
        self.x += dx
        self.y += dy
        
        # 目標位置も更新（タッチ操作との連携のため）
        self.target_x = self.x
        self.target_y = self.y
        
        # ボムの使用
        if pyxel.btnp(pyxel.KEY_X) and self.bomb > 0:
            self.use_bomb()
    
    def handle_touch_input(self):
        """
        タッチ入力を処理します。
        """
        # タッチ開始
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.touch_start_x = pyxel.mouse_x
            self.touch_start_y = pyxel.mouse_y
            self.touch_start_time = time.time()
            self.is_touching = True
            self.joystick_duration = 0
            
            # ダブルタップ検出
            current_time = time.time()
            if current_time - self.last_tap_time < DOUBLE_TAP_TIME and self.bomb > 0:
                self.use_bomb()
            self.last_tap_time = current_time
            
            # 画面上部のタップはショットのみ、下部はジョイスティック開始
            if pyxel.mouse_y < pyxel.height - CONTROL_AREA_HEIGHT:
                # 上部タップ: ショット＋移動なし
                if self.shot_cooldown == 0:
                    self.shoot()
                    self.shot_cooldown = 2  # 連射速度をさらに上げる
            else:
                # 下部タップ: 仮想ジョイスティック開始位置を設定
                self.joystick_center_x = pyxel.mouse_x
                self.joystick_center_y = pyxel.mouse_y
                self.joystick_active = True
                
                # ショットも同時に発射
                if self.shot_cooldown == 0:
                    self.shoot()
                    self.shot_cooldown = 2  # 連射速度をさらに上げる
        
        # タッチ中
        if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            # 長押しで低速移動
            if time.time() - self.touch_start_time > 0.2:
                self.is_focusing = True
            
            # タッチ中は定期的にショット
            if self.shot_cooldown == 0:
                self.shoot()
                self.shot_cooldown = 2  # 連射速度をさらに上げる
            
            # 移動制御
            if self.is_touching:
                # 現在の移動速度を決定
                current_speed = self.focus_speed if self.is_focusing else PLAYER_SPEED
                
                if self.joystick_active:
                    # ジョイスティック操作の持続時間を増加（加速のため）
                    self.joystick_duration += 1
                    
                    # 加速係数を計算（最大1.5倍までの加速）（2.0から1.5に減少）
                    acceleration = min(1.0 + self.joystick_duration / 90, 1.5)
                    
                    # ジョイスティックモード
                    dx = pyxel.mouse_x - self.joystick_center_x
                    dy = pyxel.mouse_y - self.joystick_center_y
                    
                    # ジョイスティックの距離に応じて速度を調整（最大速度を制限）
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance > 2:  # 入力感度の向上（5→2）
                        # 移動方向と速度を計算
                        normalized_dx = dx / distance
                        normalized_dy = dy / distance
                        
                        # 距離に応じた速度調整
                        # - 感度を向上（JOYSTICK_SENSITIVITY）
                        # - 最大速度倍率を向上（JOYSTICK_MAX_SPEED_FACTOR）
                        # - 持続時間による加速（acceleration）
                        speed_factor = min(distance / JOYSTICK_SENSITIVITY * JOYSTICK_MAX_SPEED_FACTOR, JOYSTICK_MAX_SPEED_FACTOR) * acceleration
                        move_speed = current_speed * speed_factor
                        
                        # 直接位置を更新（より即応性を高める）
                        self.x += normalized_dx * move_speed
                        self.y += normalized_dy * move_speed
                        
                        # 画面外に出ないように制限
                        self.x = max(0, min(self.x, pyxel.width - self.width))
                        self.y = max(0, min(self.y, pyxel.height - self.height))
                        
                        # 目標位置も更新
                        self.target_x = self.x
                        self.target_y = self.y
                else:
                    # 画面上部のタッチなら直接移動（ダイレクトタッチモード）
                    if pyxel.mouse_y < pyxel.height - CONTROL_AREA_HEIGHT:
                        # タップした位置を目標位置として設定（中心位置を合わせる）
                        self.target_x = pyxel.mouse_x - self.width / 2
                        self.target_y = pyxel.mouse_y - self.height / 2
                        
                        # 画面外に出ないように制限
                        self.target_x = max(0, min(self.target_x, pyxel.width - self.width))
                        self.target_y = max(0, min(self.target_y, pyxel.height - self.height))
                        
                        # 注：直接位置更新を削除し、updateメソッドでの滑らかな移動に任せる
        
        # タッチ終了
        if pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT):
            self.is_touching = False
            self.is_focusing = False
            self.joystick_active = False
            self.joystick_duration = 0
    
    def shoot(self):
        """
        弾を発射します。パワーレベルに応じて弾の数や配置が変化します。
        """
        center_x = self.x + self.width / 2
        top_y = self.y  # プレイヤーの先端位置
        
        # パワーレベルに応じて弾の数や配置を変更
        if self.power == 1:
            # 単発（中央）
            self.bullets.append(Bullet(center_x - 2, top_y))
        elif self.power == 2:
            # 2連射（左右）
            left_x = center_x - self.width / 4
            right_x = center_x + self.width / 4
            self.bullets.append(Bullet(left_x, top_y + 4))
            self.bullets.append(Bullet(right_x, top_y + 4))
        elif self.power == 3:
            # 3連射（中央と左右）
            left_x = center_x - self.width / 3
            right_x = center_x + self.width / 3
            self.bullets.append(Bullet(center_x - 2, top_y))
            self.bullets.append(Bullet(left_x, top_y + 4))
            self.bullets.append(Bullet(right_x, top_y + 4))
        elif self.power == 4:
            # 5連射（中央、左右、両側面）
            left_x = center_x - self.width / 3
            right_x = center_x + self.width / 3
            self.bullets.append(Bullet(center_x - 2, top_y))
            self.bullets.append(Bullet(left_x, top_y + 4))
            self.bullets.append(Bullet(right_x, top_y + 4))
            # 横方向の弾
            self.bullets.append(Bullet(self.x - 3, self.y + self.height/2, math.pi/2 + 0.5))
            self.bullets.append(Bullet(self.x + self.width, self.y + self.height/2, math.pi/2 - 0.5))
        elif self.power >= 5:
            # 7連射（最大パワー - 前方全域と斜め後方）
            left_x = center_x - self.width / 3
            right_x = center_x + self.width / 3
            self.bullets.append(Bullet(center_x - 2, top_y - 4))
            self.bullets.append(Bullet(left_x, top_y))
            self.bullets.append(Bullet(right_x, top_y))
            # 横方向の弾
            self.bullets.append(Bullet(self.x - 3, self.y + self.height/2, math.pi/2 + 0.5))
            self.bullets.append(Bullet(self.x + self.width, self.y + self.height/2, math.pi/2 - 0.5))
            # 後方向き斜め弾
            self.bullets.append(Bullet(self.x - 3, self.y + self.height*0.7, math.pi/2 + 0.8))
            self.bullets.append(Bullet(self.x + self.width, self.y + self.height*0.7, math.pi/2 - 0.8))
        
        # ショット音を再生
        pyxel.play(0, 0)
    
    def use_bomb(self):
        """
        ボムを使用します。画面上の敵弾を消し、一定時間の無敵状態になります。
        """
        if self.bomb > 0:
            self.bomb -= 1
            self.invincible = 120  # ボム使用時の無敵時間は長め
            # 実際のボム効果はゲームクラスで処理
    
    def update_options(self):
        """
        オプション（サブウェポン）の位置を更新します。
        """
        self.options = []
        
        if self.power >= 3:
            # レベル3以上でオプション追加 - 左ウィング
            left_x = self.x - self.width * 0.2
            left_y = self.y + self.height * 0.4
            self.options.append((left_x, left_y))
            
        if self.power >= 5:
            # レベル5でオプション追加 - 右ウィング
            right_x = self.x + self.width * 0.9
            right_y = self.y + self.height * 0.4
            self.options.append((right_x, right_y))
    
    def draw(self):
        """
        プレイヤーを描画します。
        """
        # アニメーションフレームの更新
        self.animation_frame = (pyxel.frame_count // 8) % 2
        
        # 無敵時間中は点滅させる
        if self.invincible == 0 or pyxel.frame_count % 4 < 2:
            # プレイヤー本体を描画
            y_offset = 0 if self.animation_frame == 0 else self.frame_offset
            
            if DEBUG and pyxel.frame_count % 60 == 0:
                print(f"描画情報: フレーム={self.animation_frame}, オフセット={y_offset}, サイズ={self.width}x{self.height}")
            
            # コンテンツチェックは削除（速度向上のため）
            # 常に完全なサイズを使用し、クリッピングをしない
            
            # 必ずプレイヤーのスプライトを描画
            pyxel.blt(
                self.x, self.y,  # 描画位置
                0,  # イメージバンク
                0, y_offset,  # 画像上の位置
                self.width, self.height,  # サイズ
                0  # 透明色（黒）
            )
            
            if DEBUG and pyxel.frame_count % 60 == 0:
                print(f"プレイヤースプライト描画: x={self.x}, y={self.y}, w={self.width}, h={self.height}, offset_y={y_offset}")
            
            # デバッグ用の描画（当たり判定の可視化）
            if DEBUG and pyxel.btn(pyxel.KEY_D):
                pyxel.circb(
                    self.x + self.width / 2,
                    self.y + self.height / 2,
                    self.hitbox_radius,
                    8  # 赤色で描画
                )
        
        # オプション（サブウェポン）の描画
        for i, (opt_x, opt_y) in enumerate(self.options):
            # オプションのフレームも本体と同期
            option_y_offset = 0 if self.animation_frame == 0 else 16
            pyxel.blt(opt_x, opt_y, 0, 40, option_y_offset, 16, 16, 0)
            
            if DEBUG and pyxel.btn(pyxel.KEY_D):
                # オプションの当たり判定（小さめ）
                pyxel.circb(opt_x + 8, opt_y + 8, 4, 12)
        
        # 弾（ビーム）の描画 - 重要：これを追加し直す
        for bullet in self.bullets:
            bullet.draw()
        
        # ボム使用時のエフェクト
        if self.bomb > 0 and pyxel.btn(pyxel.KEY_X) and pyxel.frame_count % 3 == 0:
            # ボム効果のビジュアルエフェクト
            self.use_bomb()
            
        # 移動方向に応じたエフェクト（オプション）
        if self.is_touching:
            # タッチ操作中は指示点を表示
            pyxel.circb(self.target_x + self.width / 2, self.target_y + self.height / 2, 3, 7)
            
            # ジョイスティックモードの場合は線を描画
            if self.touch_control_mode == "joystick" and self.joystick_active:
                pyxel.line(
                    self.joystick_center_x,
                    self.joystick_center_y,
                    self.target_x + self.width / 2,
                    self.target_y + self.height / 2,
                    6
                )
    
    def get_hit(self):
        """
        プレイヤーが被弾した時の処理を行います。
        
        @returns {boolean} - 被弾して残機が減ったらTrue
        """
        if self.invincible == 0:
            self.lives -= 1
            self.invincible = INVINCIBLE_TIME  # 無敵時間の設定
            self.power = max(1, self.power - 1)  # パワーダウン
            return True
        return False
    
    def power_up(self):
        """
        パワーアップアイテムを取得した時の処理を行います。
        """
        self.power = min(MAX_POWER_LEVEL, self.power + 1)
        
    def add_life(self):
        """
        残機を追加します。
        """
        self.lives += 1
        
    def add_bomb(self):
        """
        ボムを追加します。
        """
        self.bomb += 1 