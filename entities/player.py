"""
プレイヤークラスモジュール

プレイヤーキャラクターの動作、描画、状態管理を担当するクラスを定義します。
"""

import pyxel
import math

# プレイヤー関連の定数
PLAYER_SPEED = 3  # プレイヤーの移動速度
PLAYER_BULLET_SPEED = 6  # プレイヤーの弾の速度
MAX_POWER_LEVEL = 5  # 最大パワーレベル
INVINCIBLE_TIME = 60  # 無敵時間（フレーム数）
HITBOX_RADIUS = 2  # 当たり判定の半径

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
    
    def update(self):
        """
        プレイヤーの状態を更新します。
        """
        # 低速移動モードの切り替え
        self.is_focusing = pyxel.btn(pyxel.KEY_SHIFT)
        
        # 現在の移動速度を決定
        current_speed = self.focus_speed if self.is_focusing else PLAYER_SPEED
        
        # プレイヤーの移動
        if pyxel.btn(pyxel.KEY_LEFT) and self.x > 0:
            self.x -= current_speed
        if pyxel.btn(pyxel.KEY_RIGHT) and self.x < pyxel.width - self.width:
            self.x += current_speed
        if pyxel.btn(pyxel.KEY_UP) and self.y > 0:
            self.y -= current_speed
        if pyxel.btn(pyxel.KEY_DOWN) and self.y < pyxel.height - self.height:
            self.y += current_speed
        
        # ショットクールダウンを減少
        if self.shot_cooldown > 0:
            self.shot_cooldown -= 1
        
        # 弾の発射
        if pyxel.btn(pyxel.KEY_Z) and self.shot_cooldown == 0:
            self.shoot()
            self.shot_cooldown = 5  # 連射速度の調整（値が小さいほど速い）
        
        # ボムの使用
        if pyxel.btnp(pyxel.KEY_X) and self.bomb > 0:
            self.use_bomb()
        
        # 弾の更新
        for bullet in self.bullets[:]:
            if bullet.update():
                self.bullets.remove(bullet)
        
        # オプションの位置更新
        self.update_options()
        
        # 無敵時間の更新
        if self.invincible > 0:
            self.invincible -= 1
    
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