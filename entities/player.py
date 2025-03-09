"""
プレイヤークラスモジュール

プレイヤーキャラクターの動作、描画、状態管理を担当するクラスを定義します。
"""

import pyxel
import math
import time

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
        self.width = 2
        self.height = 6
        self.power = power
        self.is_active = True
    
    def update(self):
        """
        弾の状態を更新します。
        
        @returns {boolean} - 弾が画面外に出たらTrue
        """
        self.x += self.vx
        self.y += self.vy
        
        # 画面外に出たら削除フラグを立てる
        if (self.x < -self.width or self.x > pyxel.width + self.width or
            self.y < -self.height or self.y > pyxel.height + self.height):
            return True
        return False
    
    def draw(self):
        """
        弾を描画します。
        """
        pyxel.rect(self.x - self.width/2, self.y, self.width, self.height, 7)

class Player:
    """
    プレイヤークラス
    
    プレイヤーキャラクターの動作、状態管理、描画を担当します。
    """
    def __init__(self):
        """
        プレイヤーを初期化します。
        """
        self.x = pyxel.width // 2
        self.y = pyxel.height - 30
        self.width = 8
        self.height = 8
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
        
        # 弾の発射
        if pyxel.btn(pyxel.KEY_Z) and self.shot_cooldown == 0:
            self.shoot()
            self.shot_cooldown = 5  # 連射速度の調整（値が小さいほど速い）
        
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
                    self.shot_cooldown = 5
            else:
                # 下部タップ: 仮想ジョイスティック開始位置を設定
                self.joystick_center_x = pyxel.mouse_x
                self.joystick_center_y = pyxel.mouse_y
                self.joystick_active = True
                
                # ショットも同時に発射
                if self.shot_cooldown == 0:
                    self.shoot()
                    self.shot_cooldown = 5
        
        # タッチ中
        if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            # 長押しで低速移動
            if time.time() - self.touch_start_time > 0.2:
                self.is_focusing = True
            
            # タッチ中は定期的にショット
            if self.shot_cooldown == 0:
                self.shoot()
                self.shot_cooldown = 5
            
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
        
        # パワーレベルに応じて弾の数や配置を変更
        if self.power == 1:
            self.bullets.append(Bullet(center_x, self.y))
        elif self.power == 2:
            self.bullets.append(Bullet(center_x - 3, self.y))
            self.bullets.append(Bullet(center_x + 3, self.y))
        elif self.power == 3:
            self.bullets.append(Bullet(center_x, self.y))
            self.bullets.append(Bullet(center_x - 4, self.y + 2))
            self.bullets.append(Bullet(center_x + 4, self.y + 2))
        elif self.power == 4:
            self.bullets.append(Bullet(center_x, self.y))
            self.bullets.append(Bullet(center_x - 4, self.y + 2))
            self.bullets.append(Bullet(center_x + 4, self.y + 2))
            # サイド弾（少し斜めに）
            self.bullets.append(Bullet(center_x - 6, self.y + 4, math.pi/2 + 0.2))
            self.bullets.append(Bullet(center_x + 6, self.y + 4, math.pi/2 - 0.2))
        elif self.power >= 5:
            # 最大パワーレベル
            self.bullets.append(Bullet(center_x, self.y))
            self.bullets.append(Bullet(center_x - 4, self.y + 2))
            self.bullets.append(Bullet(center_x + 4, self.y + 2))
            # サイド弾（少し斜めに）
            self.bullets.append(Bullet(center_x - 6, self.y + 4, math.pi/2 + 0.2))
            self.bullets.append(Bullet(center_x + 6, self.y + 4, math.pi/2 - 0.2))
            # 後方弾
            self.bullets.append(Bullet(center_x - 8, self.y + 6, math.pi/2 + 0.4))
            self.bullets.append(Bullet(center_x + 8, self.y + 6, math.pi/2 - 0.4))
    
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
        # パワーレベルに応じてオプションを更新
        self.options = []
        
        if self.power >= 3:
            # レベル3以上でオプション追加
            self.options.append((self.x - 12, self.y + 8))
            
        if self.power >= 5:
            # レベル5でオプション追加
            self.options.append((self.x + 12, self.y + 8))
    
    def draw(self):
        """
        プレイヤーを描画します。
        """
        # 無敵時間中は点滅させる
        if self.invincible == 0 or pyxel.frame_count % 4 < 2:
            # プレイヤー本体
            pyxel.blt(self.x, self.y, 0, 0, 0, self.width, self.height, 0)
            
            # 低速移動時の当たり判定表示
            if self.is_focusing:
                pyxel.circ(self.x + self.width/2, self.y + self.height/2, 
                          self.hitbox_radius, 8)
            
            # オプションの描画
            for opt_x, opt_y in self.options:
                pyxel.blt(opt_x, opt_y, 0, 8, 0, 6, 6, 0)
        
        # 弾の描画
        for bullet in self.bullets:
            bullet.draw()
            
        # 仮想ジョイスティックの描画（タッチ中のみ）
        if self.joystick_active and self.is_touching:
            # ジョイスティックの基点
            pyxel.circb(self.joystick_center_x, self.joystick_center_y, 20, 13)
            
            # 現在の入力位置
            dx = pyxel.mouse_x - self.joystick_center_x
            dy = pyxel.mouse_y - self.joystick_center_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # 加速状態のフィードバック
            acceleration_color = 7  # 通常は白
            if self.joystick_duration > 45:  # 30から45に増加（加速までの時間延長）
                # 加速中は明るい色に
                acceleration_color = 10 if pyxel.frame_count % 6 < 3 else 11
            
            if distance > 0:
                # 最大半径を超えないように
                max_radius = 20
                display_x = self.joystick_center_x + dx * min(distance, max_radius) / distance
                display_y = self.joystick_center_y + dy * min(distance, max_radius) / distance
                
                # 入力スティック
                pyxel.circ(display_x, display_y, 5, acceleration_color)
                pyxel.line(self.joystick_center_x, self.joystick_center_y, display_x, display_y, acceleration_color)
                
                # 感度と速度をフィードバック
                speed_factor = min(distance / JOYSTICK_SENSITIVITY * JOYSTICK_MAX_SPEED_FACTOR, JOYSTICK_MAX_SPEED_FACTOR)
                speed_radius = 5 + speed_factor * 3  # 速度に応じてサイズ変化
                if speed_factor > 1.3:  # 1.5から1.3に減少（エフェクト表示閾値を下げる）
                    # 高速時は追加エフェクト
                    pyxel.circb(display_x, display_y, speed_radius, acceleration_color)
    
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