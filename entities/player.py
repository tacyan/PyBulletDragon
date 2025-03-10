"""
プレイヤークラスモジュール

プレイヤーキャラクターの動作、描画、状態管理を担当するクラスを定義します。
"""

import pyxel
import math
import time
import os
from utils.image_loader import DEBUG

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
        # スペースシャトルの弾を描画
        pyxel.blt(self.x - 2, self.y - 3, 0, 32, 0, 5, 6, 0)
        
        # 発射エフェクト（オプション）
        if self.animation_frame < 2:
            # 明るいエフェクト（点滅）
            pyxel.pset(self.x, self.y + self.height - 1, 7)  # 白色の点

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
            # PILを使って画像サイズを直接取得（最も信頼性が高い方法）
            img_path = os.path.join("resources", "player.png")
            if os.path.exists(img_path):
                try:
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
                        print(f"PIL画像サイズ取得エラー: {e}")
                    # PILでエラーが発生した場合は後続のピクセルスキャン方法を試みる
            
            # イメージバンク0の内容をスキャンして画像サイズを検出
            max_x = 0
            max_y = 0
            min_x = 999
            min_y = 999
            
            # 非透明ピクセルの範囲を検出（より正確な方法）
            non_transparent_pixels = 0
            for y in range(64):
                for x in range(64):
                    if pyxel.images[0].pget(x, y) != 0:  # 非透明ピクセルを見つけた
                        non_transparent_pixels += 1
                        max_x = max(max_x, x)
                        max_y = max(max_y, y)
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
            
            if DEBUG:
                print(f"ピクセルスキャン: 非透明ピクセル数={non_transparent_pixels}")
                print(f"範囲: ({min_x},{min_y})-({max_x},{max_y})")
            
            # 実際の幅と高さを計算
            if non_transparent_pixels > 0 and max_x >= min_x and max_y >= min_y:
                width = max_x - min_x + 1
                height = max_y - min_y + 1
                
                # 最小サイズを確保
                width = max(16, width)
                height = max(16, height)
                
                if DEBUG:
                    print(f"検出されたプレイヤー画像サイズ: {width}x{height}")
                
                # デフォルトより大きいサイズの場合のみ採用
                if width > 8 and height > 8:
                    self.width = width
                    self.height = height
                    self.frame_offset = height
                    return
            
            # 以上の方法で失敗した場合はデフォルトサイズを使用
            self.width = 32  # デフォルト幅
            self.height = 32  # デフォルト高さ
            self.frame_offset = self.height
            
            if DEBUG:
                print(f"デフォルトサイズを使用: {self.width}x{self.height}")
            
        except Exception as e:
            if DEBUG:
                print(f"画像サイズ検出中にエラーが発生しました: {e}")
                import traceback
                traceback.print_exc()
            
            # エラー時はデフォルトサイズを使用
            self.width = 32  # デフォルト幅を大きめに
            self.height = 32  # デフォルト高さを大きめに
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
                        # タップした位置に直接移動（中心位置を合わせる）
                        self.target_x = pyxel.mouse_x - self.width / 2
                        self.target_y = pyxel.mouse_y - self.height / 2
                        
                        # 画面外に出ないように制限
                        self.target_x = max(0, min(self.target_x, pyxel.width - self.width))
                        self.target_y = max(0, min(self.target_y, pyxel.height - self.height))
                        
                        # 直接位置を更新（より即応性を高める）
                        self.x = self.target_x
                        self.y = self.target_y
        
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
            
            # リソースの検証（透明でないピクセルがあるか確認）
            has_content = False
            non_transparent_pixels = 0
            
            # 効率的に内容をチェック（サンプリング）
            check_step = max(1, min(self.width, self.height) // 4)
            for check_y in range(0, self.height, check_step):
                for check_x in range(0, self.width, check_step):
                    if pyxel.images[0].pget(check_x, check_y + y_offset) != 0:
                        has_content = True
                        non_transparent_pixels += 1
            
            if DEBUG and pyxel.frame_count % 60 == 0:
                print(f"コンテンツチェック: 非透明ピクセル数={non_transparent_pixels}, 有効={has_content}")
            
            # PILから直接サイズを取得する代替手段（非常に小さいサイズの場合）
            if self.width <= 8 or self.height <= 8:
                try:
                    img_path = os.path.join("resources", "player.png")
                    if os.path.exists(img_path):
                        from PIL import Image
                        img = Image.open(img_path)
                        pil_width, pil_height = img.size
                        
                        # 最大64x64に制限
                        if pil_width > 64 or pil_height > 64:
                            ratio = min(64 / pil_width, 64 / pil_height)
                            pil_width = int(pil_width * ratio)
                            pil_height = int(pil_height * ratio)
                        
                        # 大きすぎなければPILからのサイズを使用
                        if pil_width > 8 and pil_height > 8:
                            if DEBUG:
                                print(f"小さすぎるサイズを検出: {self.width}x{self.height} → PILサイズ: {pil_width}x{pil_height}を使用")
                            self.width = pil_width
                            self.height = pil_height
                            self.frame_offset = pil_height
                except Exception as e:
                    if DEBUG:
                        print(f"PILサイズ取得エラー: {e}")
            
            # 内容が空でも強制的に表示する（デバッグ用）
            display_anyway = True
            
            if has_content or display_anyway:
                # プレイヤーのスプライトを描画
                pyxel.blt(self.x, self.y, 0, 0, y_offset, self.width, self.height, 0)
                
                if DEBUG and pyxel.frame_count % 60 == 0:
                    print(f"プレイヤースプライト描画: x={self.x}, y={self.y}, w={self.width}, h={self.height}, offset_y={y_offset}")
            else:
                # コンテンツが見つからない場合の対応（エラー時の表示）
                if DEBUG and pyxel.frame_count % 60 == 0:
                    print(f"警告: プレイヤースプライトにコンテンツがありません！ バンク0: (0,{y_offset})-({self.width},{y_offset+self.height})")
                
                # 代替表示（シンプルな四角形）
                pyxel.rectb(self.x, self.y, self.width, self.height, 7)
                pyxel.line(self.x, self.y, self.x + self.width - 1, self.y + self.height - 1, 7)
                pyxel.line(self.x, self.y + self.height - 1, self.x + self.width - 1, self.y, 7)
            
            # エンジン推進エフェクト（下部）- 画像自体にエンジン炎が含まれているかも
            engine_y = self.y + self.height
            engine_center_x = self.x + self.width / 2
            
            # 追加のエンジンエフェクト（オプション）
            if pyxel.frame_count % 8 < 4:
                # 明るいエフェクト
                pyxel.line(engine_center_x - 2, engine_y, 
                          engine_center_x - 4, engine_y + 3, 7)
                pyxel.line(engine_center_x + 2, engine_y, 
                          engine_center_x + 4, engine_y + 3, 7)
            else:
                # 暗いエフェクト
                pyxel.line(engine_center_x - 2, engine_y, 
                          engine_center_x - 3, engine_y + 2, 10)
                pyxel.line(engine_center_x + 2, engine_y, 
                          engine_center_x + 3, engine_y + 2, 10)
            
            # 低速移動時の当たり判定表示
            if self.is_focusing:
                pyxel.circb(self.x + self.width/2, self.y + self.height/2, self.hitbox_radius, 7)
            
            # オプションの描画（小型のサブウェポン）
            for opt_x, opt_y in self.options:
                # オプションのエンジン炎も同様にアニメーション
                if pyxel.frame_count % 8 < 4:
                    # 明るいエフェクト
                    pyxel.line(opt_x + 2, opt_y + 5, opt_x + 1, opt_y + 7, 7)
                    pyxel.line(opt_x + 2, opt_y + 5, opt_x + 3, opt_y + 7, 7)
                else:
                    # 暗いエフェクト
                    pyxel.line(opt_x + 2, opt_y + 5, opt_x + 1, opt_y + 6, 10)
                    pyxel.line(opt_x + 2, opt_y + 5, opt_x + 3, opt_y + 6, 10)
                
                # オプションを描画
                pyxel.blt(opt_x, opt_y, 0, 8, 0, 5, 6, 0)
        
        # 弾の描画
        for bullet in self.bullets:
            bullet.draw()
    
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