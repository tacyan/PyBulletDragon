"""
ボスクラスモジュール

ボスの動作、弾幕パターン、描画、状態管理を担当するクラスを定義します。
"""

import pyxel
import math
import random

# ボス関連の定数
BOSS_INITIAL_HP = 1000  # ボスの初期HP
ENEMY_BULLET_SPEED = 2  # 敵の弾の基本速度
SPELL_CARD_TIME = 1800  # スペルカードの制限時間（フレーム数）

class Bullet:
    """
    敵の弾クラス
    
    ボスが発射する弾の動作や描画を管理します。
    """
    def __init__(self, x, y, vx, vy, bullet_type=0):
        """
        弾を初期化します。
        
        @param {number} x - 弾のX座標
        @param {number} y - 弾のY座標
        @param {number} vx - X方向の速度
        @param {number} vy - Y方向の速度
        @param {number} bullet_type - 弾の種類（描画や効果に影響）
        """
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = 2  # 弾の半径（描画用）
        self.hitbox_radius = 2  # 当たり判定の半径
        self.bullet_type = bullet_type
        self.is_active = True
        
    def update(self):
        """
        弾の状態を更新します。
        
        @returns {boolean} - 弾が画面外に出たらTrue
        """
        self.x += self.vx
        self.y += self.vy
        
        # 画面外に出たら削除フラグを立てる
        if (self.x < -10 or self.x > pyxel.width + 10 or
            self.y < -10 or self.y > pyxel.height + 10):
            return True
        return False
        
    def draw(self):
        """
        弾を描画します。
        """
        # 弾の種類に応じて色や形状を変える
        if self.bullet_type == 0:
            pyxel.circ(self.x, self.y, self.radius, 8)  # 赤い丸い弾
        elif self.bullet_type == 1:
            pyxel.circ(self.x, self.y, self.radius + 1, 9)  # 緑の大きい丸い弾
        elif self.bullet_type == 2:
            pyxel.circ(self.x, self.y, self.radius, 10)  # 青い丸い弾
        elif self.bullet_type == 3:
            pyxel.circ(self.x, self.y, self.radius, 11)  # 紫の丸い弾
        elif self.bullet_type == 4:
            # 星型の弾（簡易的に表現）
            pyxel.circ(self.x, self.y, self.radius, 14)
            pyxel.pset(self.x, self.y, 7)

class SpellCard:
    """
    スペルカードクラス
    
    ボスの特殊攻撃パターン（スペルカード）を管理します。
    """
    def __init__(self, name, hp, duration=SPELL_CARD_TIME):
        """
        スペルカードを初期化します。
        
        @param {string} name - スペルカードの名前
        @param {number} hp - スペルカードのHP
        @param {number} duration - スペルカードの制限時間（フレーム数）
        """
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.duration = duration
        self.time_left = duration
        self.is_active = True
        
    def update(self):
        """
        スペルカードの状態を更新します。
        
        @returns {boolean} - スペルカードが終了したらTrue
        """
        self.time_left -= 1
        
        # 時間切れまたはHPが0になったら終了
        if self.time_left <= 0 or self.hp <= 0:
            self.is_active = False
            return True
        return False
        
    def get_hit(self, damage=1):
        """
        スペルカードがダメージを受けたときの処理を行います。
        
        @param {number} damage - 受けるダメージ量
        @returns {boolean} - HPが0になったらTrue
        """
        self.hp -= damage
        return self.hp <= 0

class Boss:
    """
    ボスクラス
    
    ボスの動作、状態管理、弾幕パターン、描画を担当します。
    """
    def __init__(self):
        """
        ボスを初期化します。
        """
        self.x = pyxel.width // 2 - 16
        self.y = 40
        self.width = 32
        self.height = 32
        self.hp = BOSS_INITIAL_HP
        self.max_hp = BOSS_INITIAL_HP
        self.bullets = []
        self.pattern = 0  # 現在の弾幕パターン
        self.pattern_timer = 0  # パターン切り替えタイマー
        self.move_timer = 0  # 移動用タイマー
        self.phase = 1  # ボスのフェーズ（HPによって変化）
        self.spell_cards = self.create_spell_cards()  # スペルカード配列
        self.current_spell = None  # 現在のスペルカード
        self.is_spell_card_active = False  # スペルカードモード
        self.attack_cooldown = 0  # 攻撃クールダウン
        
    def create_spell_cards(self):
        """
        スペルカードのリストを作成します。
        
        @returns {list} - スペルカードのリスト
        """
        # 各フェーズに1つずつスペルカードを設定
        return [
            SpellCard("紅蓮「スカーレットレーザー」", 400),
            SpellCard("蝶符「バタフライストーム」", 600),
            SpellCard("禁忌「レッドマジック」", 800)
        ]
        
    def update(self, player):
        """
        ボスの状態を更新します。
        
        @param {Player} player - プレイヤーオブジェクト（自機狙いなどに使用）
        """
        # ボスの移動パターン
        self.update_movement()
        
        # フェーズの更新チェック
        self.check_phase_transition()
        
        # スペルカードの管理
        self.update_spell_card()
        
        # 弾幕生成
        self.update_attack_pattern(player)
        
        # 弾の更新
        self.update_bullets()
        
    def update_movement(self):
        """
        ボスの移動パターンを更新します。
        """
        self.move_timer += 1
        
        # フェーズに応じた動きパターン
        if self.phase == 1:
            # フェーズ1: 穏やかな左右移動
            self.x = pyxel.width // 2 - 16 + math.sin(self.move_timer / 60) * 40
        elif self.phase == 2:
            # フェーズ2: やや速い左右移動
            self.x = pyxel.width // 2 - 16 + math.sin(self.move_timer / 40) * 60
            # 時々上下移動も追加
            if 400 < self.move_timer < 600:
                self.y = 40 + math.sin(self.move_timer / 30) * 20
        elif self.phase == 3:
            # フェーズ3: 不規則な動き
            self.x = pyxel.width // 2 - 16 + math.sin(self.move_timer / 30) * 70
            self.y = 40 + math.sin(self.move_timer / 20) * 30
            
        # 移動タイマーのリセット
        if self.move_timer > 1200:  # 20秒周期
            self.move_timer = 0
            
    def check_phase_transition(self):
        """
        HPに基づいてフェーズ遷移をチェックします。
        """
        # フェーズ遷移の条件
        if self.hp < self.max_hp * 0.6 and self.phase == 1:
            self.phase = 2  # 体力60%以下でフェーズ2へ
            self.activate_spell_card(1)  # フェーズ2のスペルカード
        elif self.hp < self.max_hp * 0.3 and self.phase == 2:
            self.phase = 3  # 体力30%以下でフェーズ3へ
            self.activate_spell_card(2)  # フェーズ3のスペルカード
            
    def activate_spell_card(self, index):
        """
        指定したインデックスのスペルカードをアクティブにします。
        
        @param {number} index - アクティブにするスペルカードのインデックス
        """
        self.current_spell = self.spell_cards[index]
        self.is_spell_card_active = True
        self.bullets = []  # 弾をクリア
            
    def update_spell_card(self):
        """
        現在のスペルカードの状態を更新します。
        """
        if self.is_spell_card_active and self.current_spell:
            if self.current_spell.update():
                # スペルカード終了
                self.is_spell_card_active = False
                self.current_spell = None
                
    def update_attack_pattern(self, player):
        """
        現在のフェーズとパターンに基づいて攻撃パターンを更新します。
        
        @param {Player} player - プレイヤーオブジェクト（自機狙いなどに使用）
        """
        # クールダウン減少
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            return
            
        # パターン切り替えタイマー
        self.pattern_timer += 1
        if self.pattern_timer > 180:  # 3秒ごとにパターン変更
            self.pattern = (self.pattern + 1) % 3
            self.pattern_timer = 0
            
        # スペルカードがアクティブならスペルカード専用パターン
        if self.is_spell_card_active:
            self.shoot_spell_card_pattern(player)
        else:
            # 通常の弾幕パターン
            if self.phase == 1:
                if pyxel.frame_count % 20 == 0:
                    self.shoot_pattern(self.pattern, player)
            elif self.phase == 2:
                if pyxel.frame_count % 15 == 0:
                    self.shoot_pattern(self.pattern, player)
                    # フェーズ2では追加の弾幕
                    if pyxel.frame_count % 45 == 0:
                        self.shoot_circle(8)
            elif self.phase == 3:
                if pyxel.frame_count % 10 == 0:
                    self.shoot_pattern(self.pattern, player)
                    # フェーズ3ではさらに弾幕を増やす
                    if pyxel.frame_count % 30 == 0:
                        self.shoot_circle(12)
                    if pyxel.frame_count % 90 == 0:
                        self.shoot_spiral(20, 2)
                        
    def shoot_spell_card_pattern(self, player):
        """
        現在のスペルカードに基づいた弾幕パターンを発射します。
        
        @param {Player} player - プレイヤーオブジェクト
        """
        # スペルカードのインデックスによってパターンを分ける
        if self.current_spell == self.spell_cards[0]:
            # 「スカーレットレーザー」: 扇状の弾幕＋自機狙い
            if pyxel.frame_count % 30 == 0:
                self.shoot_fan(10, math.pi/3)
            if pyxel.frame_count % 60 == 0:
                self.shoot_aimed(player, 5)
        elif self.current_spell == self.spell_cards[1]:
            # 「バタフライストーム」: 蝶の形に広がる弾幕
            if pyxel.frame_count % 20 == 0:
                self.shoot_butterfly(15)
        elif self.current_spell == self.spell_cards[2]:
            # 「レッドマジック」: 複雑な円形パターン
            if pyxel.frame_count % 15 == 0:
                self.shoot_complex_circle(20, 0.1)
                
    def shoot_pattern(self, pattern, player):
        """
        指定されたパターンの弾幕を発射します。
        
        @param {number} pattern - 弾幕パターンのインデックス
        @param {Player} player - プレイヤーオブジェクト
        """
        boss_center_x = self.x + self.width / 2
        boss_center_y = self.y + self.height / 2
        
        if pattern == 0:
            # パターン0: 扇状の弾
            angle_count = 5 if self.phase == 1 else (7 if self.phase == 2 else 9)
            for i in range(angle_count):
                angle = math.pi / 2 - (math.pi / 4) + (math.pi / 2) * (i / (angle_count - 1))
                bullet = Bullet(
                    boss_center_x,
                    boss_center_y + self.height/2,
                    math.cos(angle) * ENEMY_BULLET_SPEED,
                    math.sin(angle) * ENEMY_BULLET_SPEED,
                    0  # 弾の種類
                )
                self.bullets.append(bullet)
        elif pattern == 1:
            # パターン1: 自機狙い
            player_center_x = player.x + player.width / 2
            player_center_y = player.y + player.height / 2
            angle = math.atan2(
                player_center_y - boss_center_y,
                player_center_x - boss_center_x
            )
            speed = ENEMY_BULLET_SPEED * (1.0 if self.phase == 1 else (1.2 if self.phase == 2 else 1.5))
            for i in range(-1, 2):  # -1, 0, 1
                offset = i * 0.2  # 角度オフセット
                bullet = Bullet(
                    boss_center_x,
                    boss_center_y,
                    math.cos(angle + offset) * speed,
                    math.sin(angle + offset) * speed,
                    1  # 弾の種類
                )
                self.bullets.append(bullet)
        elif pattern == 2:
            # パターン2: ランダム方向の複数の弾
            for _ in range(3 if self.phase == 1 else (5 if self.phase == 2 else 7)):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(1, ENEMY_BULLET_SPEED)
                bullet = Bullet(
                    boss_center_x,
                    boss_center_y,
                    math.cos(angle) * speed,
                    math.sin(angle) * speed,
                    2  # 弾の種類
                )
                self.bullets.append(bullet)
                
    def shoot_circle(self, count):
        """
        円形に弾を発射します。
        
        @param {number} count - 発射する弾の数
        """
        boss_center_x = self.x + self.width / 2
        boss_center_y = self.y + self.height / 2
        
        for i in range(count):
            angle = (i / count) * (math.pi * 2)
            bullet = Bullet(
                boss_center_x,
                boss_center_y,
                math.cos(angle) * ENEMY_BULLET_SPEED,
                math.sin(angle) * ENEMY_BULLET_SPEED,
                3  # 弾の種類
            )
            self.bullets.append(bullet)
            
    def shoot_fan(self, count, angle_width):
        """
        扇状に弾を発射します。
        
        @param {number} count - 発射する弾の数
        @param {number} angle_width - 扇の角度幅（ラジアン）
        """
        boss_center_x = self.x + self.width / 2
        boss_center_y = self.y + self.height / 2
        
        # 下向きを中心とした扇状
        center_angle = math.pi / 2  # 下向き
        
        for i in range(count):
            angle = center_angle - angle_width/2 + angle_width * (i / (count - 1))
            speed = ENEMY_BULLET_SPEED * 1.2
            bullet = Bullet(
                boss_center_x,
                boss_center_y,
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                0  # 弾の種類
            )
            self.bullets.append(bullet)
            
    def shoot_aimed(self, player, count):
        """
        自機狙いの弾を発射します。
        
        @param {Player} player - プレイヤーオブジェクト
        @param {number} count - 発射する弾の数
        """
        boss_center_x = self.x + self.width / 2
        boss_center_y = self.y + self.height / 2
        player_center_x = player.x + player.width / 2
        player_center_y = player.y + player.height / 2
        
        # 自機への角度を計算
        angle = math.atan2(
            player_center_y - boss_center_y,
            player_center_x - boss_center_x
        )
        
        # 複数の弾を円形に配置して、徐々に広がるように
        for i in range(count):
            offset_angle = (i / count) * (math.pi * 2)
            offset_x = math.cos(offset_angle) * 5
            offset_y = math.sin(offset_angle) * 5
            
            bullet = Bullet(
                boss_center_x + offset_x,
                boss_center_y + offset_y,
                math.cos(angle) * ENEMY_BULLET_SPEED,
                math.sin(angle) * ENEMY_BULLET_SPEED,
                1  # 弾の種類
            )
            self.bullets.append(bullet)
            
    def shoot_butterfly(self, count):
        """
        蝶の形状に弾を発射します。
        
        @param {number} count - 発射する弾の数
        """
        boss_center_x = self.x + self.width / 2
        boss_center_y = self.y + self.height / 2
        
        # 蝶の形状（簡易的な表現）
        for i in range(count):
            t = (i / count) * (math.pi * 2)
            # 蝶の数式（簡略化したバージョン）
            r = math.sin(2 * t) * 15
            
            angle = t
            bullet = Bullet(
                boss_center_x + math.cos(t) * r,
                boss_center_y + math.sin(t) * r,
                math.cos(angle) * ENEMY_BULLET_SPEED * 0.8,
                math.sin(angle) * ENEMY_BULLET_SPEED * 0.8,
                4  # 弾の種類（星型）
            )
            self.bullets.append(bullet)
            
    def shoot_spiral(self, count, spirals=1):
        """
        螺旋状に弾を発射します。
        
        @param {number} count - 発射する弾の数
        @param {number} spirals - 螺旋の数
        """
        boss_center_x = self.x + self.width / 2
        boss_center_y = self.y + self.height / 2
        
        base_angle = pyxel.frame_count / 30  # 回転する基本角度
        
        for i in range(count):
            for s in range(spirals):
                angle = base_angle + (i / count) * (math.pi * 2) + (s / spirals) * (math.pi * 2)
                bullet = Bullet(
                    boss_center_x,
                    boss_center_y,
                    math.cos(angle) * ENEMY_BULLET_SPEED,
                    math.sin(angle) * ENEMY_BULLET_SPEED,
                    s % 4  # 弾の種類を螺旋ごとに変える
                )
                self.bullets.append(bullet)
                
    def shoot_complex_circle(self, count, rotation_speed):
        """
        複雑な円形パターンの弾を発射します。
        
        @param {number} count - 発射する弾の数
        @param {number} rotation_speed - 回転速度
        """
        boss_center_x = self.x + self.width / 2
        boss_center_y = self.y + self.height / 2
        
        base_angle = pyxel.frame_count * rotation_speed
        
        for i in range(count):
            angle = base_angle + (i / count) * (math.pi * 2)
            # 内側と外側の2重円
            for radius in [1.0, 1.5]:
                bullet = Bullet(
                    boss_center_x,
                    boss_center_y,
                    math.cos(angle) * ENEMY_BULLET_SPEED * radius,
                    math.sin(angle) * ENEMY_BULLET_SPEED * radius,
                    int(angle * 3) % 4  # 弾の種類
                )
                self.bullets.append(bullet)
            
    def update_bullets(self):
        """
        すべての弾の状態を更新します。
        """
        for bullet in self.bullets[:]:
            if bullet.update():
                self.bullets.remove(bullet)
                
    def draw(self):
        """
        ボスを描画します。
        """
        # フェーズに応じた色
        color = 8 if self.phase == 1 else (9 if self.phase == 2 else 10)
        
        # ボス本体
        pyxel.rect(self.x, self.y, self.width, self.height, color)
        
        # 目や翼など、ドラゴンらしい特徴を追加
        pyxel.rect(self.x + 5, self.y + 8, 5, 5, 7)  # 左目
        pyxel.rect(self.x + self.width - 10, self.y + 8, 5, 5, 7)  # 右目
        
        # 翼の描画
        pyxel.tri(
            self.x, self.y + self.height // 2,
            self.x - 10, self.y + self.height // 3,
            self.x - 5, self.y + self.height // 2 + 10,
            color
        )
        pyxel.tri(
            self.x + self.width, self.y + self.height // 2,
            self.x + self.width + 10, self.y + self.height // 3,
            self.x + self.width + 5, self.y + self.height // 2 + 10,
            color
        )
        
        # 体力ゲージ
        self.draw_hp_gauge()
        
        # スペルカード名の表示
        if self.is_spell_card_active and self.current_spell:
            name = self.current_spell.name
            pyxel.text(pyxel.width // 2 - len(name) * 2, 20, name, 7)
            
            # スペルカードの残り時間ゲージ
            time_ratio = self.current_spell.time_left / self.current_spell.duration
            gauge_width = int(time_ratio * (pyxel.width - 40))
            pyxel.rect(20, 30, pyxel.width - 40, 2, 1)
            pyxel.rect(20, 30, gauge_width, 2, 11)  # 紫色
        
        # 弾の描画
        for bullet in self.bullets:
            bullet.draw()
            
    def draw_hp_gauge(self):
        """
        ボスのHPゲージを描画します。
        """
        gauge_width = int((self.hp / self.max_hp) * (pyxel.width - 20))
        pyxel.rect(10, 10, pyxel.width - 20, 5, 1)  # ゲージ背景
        
        # フェーズに応じたゲージの色
        gauge_color = 8 if self.phase == 1 else (9 if self.phase == 2 else 10)
        pyxel.rect(10, 10, gauge_width, 5, gauge_color)  # 現在の体力
        
        # スペルカード時は特別な表示
        if self.is_spell_card_active and self.current_spell:
            spell_gauge_width = int((self.current_spell.hp / self.current_spell.max_hp) * (pyxel.width - 20))
            pyxel.rect(10, 15, spell_gauge_width, 3, 11)  # スペルカードHP（紫）
            
    def get_hit(self, damage=1):
        """
        ボスがダメージを受けたときの処理を行います。
        
        @param {number} damage - 受けるダメージ量
        @returns {boolean} - HPが0になったらTrue
        """
        # スペルカードアクティブ時はスペルカードにダメージ
        if self.is_spell_card_active and self.current_spell:
            if self.current_spell.get_hit(damage):
                self.is_spell_card_active = False
                self.current_spell = None
        else:
            # 通常時はボス本体にダメージ
            self.hp -= damage
            
        # HP切れでゲーム終了
        return self.hp <= 0 