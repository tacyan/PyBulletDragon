"""
エフェクトクラスモジュール

ゲーム内の視覚効果（爆発、ヒットエフェクトなど）を担当するクラスを定義します。
"""

import pyxel
import math
import random

# エフェクトの種類
EFFECT_TYPE_EXPLOSION = 0  # 爆発
EFFECT_TYPE_HIT = 1        # ヒットエフェクト
EFFECT_TYPE_SPAWN = 2      # 出現エフェクト
EFFECT_TYPE_BOMB = 3       # ボムエフェクト

class Effect:
    """
    エフェクトクラス
    
    ゲーム内の視覚効果（爆発、ヒット、出現など）の描画と管理を担当します。
    """
    def __init__(self, x, y, effect_type, size=10, duration=30):
        """
        エフェクトを初期化します。
        
        @param {number} x - エフェクトのX座標
        @param {number} y - エフェクトのY座標
        @param {number} effect_type - エフェクトの種類
        @param {number} size - エフェクトのサイズ
        @param {number} duration - エフェクトの持続時間（フレーム数）
        """
        self.x = x
        self.y = y
        self.effect_type = effect_type
        self.size = size
        self.duration = duration
        self.timer = 0
        self.particles = []
        
        # エフェクトの種類に応じたパーティクル生成
        self.generate_particles()
        
    def generate_particles(self):
        """
        エフェクトの種類に応じたパーティクルを生成します。
        """
        if self.effect_type == EFFECT_TYPE_EXPLOSION:
            # 爆発エフェクト: 四方八方にパーティクルが飛び散る
            for _ in range(20):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(0.5, 2.0)
                size = random.uniform(1, 3)
                lifetime = random.randint(10, self.duration)
                color = random.choice([8, 9, 10])  # 赤、緑、青のランダム
                
                self.particles.append({
                    'x': self.x,
                    'y': self.y,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'size': size,
                    'color': color,
                    'lifetime': lifetime,
                    'timer': 0
                })
                
        elif self.effect_type == EFFECT_TYPE_HIT:
            # ヒットエフェクト: 小さな光の粒が少し飛び散る
            for _ in range(5):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(0.3, 1.0)
                size = random.uniform(0.5, 1.5)
                lifetime = random.randint(5, 15)
                color = 7  # 白色
                
                self.particles.append({
                    'x': self.x,
                    'y': self.y,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'size': size,
                    'color': color,
                    'lifetime': lifetime,
                    'timer': 0
                })
                
        elif self.effect_type == EFFECT_TYPE_SPAWN:
            # 出現エフェクト: 中心から外側に広がる円
            self.spawn_ring_timer = 0
            self.spawn_ring_max = 20
            
        elif self.effect_type == EFFECT_TYPE_BOMB:
            # ボムエフェクト: スクリーン全体に広がる波動
            self.bomb_wave_radius = 0
            self.bomb_max_radius = max(pyxel.width, pyxel.height) * 1.5
            
            # ボム使用時の追加パーティクル
            for _ in range(50):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(1, 4)
                size = random.uniform(1, 4)
                lifetime = random.randint(20, self.duration)
                color = random.choice([7, 11, 12])  # 白、紫、水色
                
                self.particles.append({
                    'x': self.x,
                    'y': self.y,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'size': size,
                    'color': color,
                    'lifetime': lifetime,
                    'timer': 0
                })
    
    def update(self):
        """
        エフェクトの状態を更新します。
        
        @returns {boolean} - エフェクトが終了したらTrue
        """
        self.timer += 1
        
        # 持続時間が経過したら終了
        if self.timer >= self.duration:
            return True
            
        # エフェクトの種類に応じた更新処理
        if self.effect_type == EFFECT_TYPE_EXPLOSION or self.effect_type == EFFECT_TYPE_HIT:
            # パーティクルの更新
            for particle in self.particles[:]:
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['timer'] += 1
                
                # 重力効果（下に落ちる）
                if self.effect_type == EFFECT_TYPE_EXPLOSION:
                    particle['vy'] += 0.05
                
                # 寿命が尽きたらパーティクル削除
                if particle['timer'] >= particle['lifetime']:
                    self.particles.remove(particle)
                    
        elif self.effect_type == EFFECT_TYPE_SPAWN:
            # 出現エフェクトの更新
            self.spawn_ring_timer += 1
            
        elif self.effect_type == EFFECT_TYPE_BOMB:
            # ボムエフェクトの更新
            self.bomb_wave_radius += (self.bomb_max_radius / self.duration) * 2
            
        return False
    
    def draw(self):
        """
        エフェクトを描画します。
        """
        if self.effect_type == EFFECT_TYPE_EXPLOSION or self.effect_type == EFFECT_TYPE_HIT:
            # パーティクルの描画
            for particle in self.particles:
                # 透明度の計算（寿命が尽きるにつれて透明に）
                alpha = 1.0 - (particle['timer'] / particle['lifetime'])
                
                # サイズの計算（時間とともに小さくなる）
                current_size = particle['size'] * alpha
                if current_size > 0:
                    pyxel.circ(particle['x'], particle['y'], current_size, particle['color'])
                    
        elif self.effect_type == EFFECT_TYPE_SPAWN:
            # 出現エフェクト: 中心から外側に広がる円
            ring_progress = self.spawn_ring_timer / self.spawn_ring_max
            ring_radius = self.size * ring_progress
            
            if ring_radius > 0:
                pyxel.circb(self.x, self.y, ring_radius, 7)  # 白い円
                
                # 二重の円
                if ring_radius > 2:
                    pyxel.circb(self.x, self.y, ring_radius - 2, 11)  # 内側の円は紫
                    
        elif self.effect_type == EFFECT_TYPE_BOMB:
            # ボムエフェクト: 画面全体に広がる波動
            # 波動の色は時間によって変化
            color_cycle = [7, 11, 12, 6]  # 白、紫、水色、薄緑
            color_index = (self.timer // 3) % len(color_cycle)
            
            # 波動の描画（同心円）
            for i in range(3):
                offset = i * 10
                if self.bomb_wave_radius - offset > 0:
                    pyxel.circb(self.x, self.y, self.bomb_wave_radius - offset, 
                              color_cycle[(color_index + i) % len(color_cycle)])
            
            # パーティクルの描画
            for particle in self.particles:
                # 透明度の計算
                alpha = 1.0 - (particle['timer'] / particle['lifetime'])
                current_size = particle['size'] * alpha
                if current_size > 0:
                    pyxel.circ(particle['x'], particle['y'], current_size, particle['color'])
                    
    @staticmethod
    def create_explosion(x, y, size=10):
        """
        爆発エフェクトを生成するファクトリメソッド
        
        @param {number} x - エフェクトのX座標
        @param {number} y - エフェクトのY座標
        @param {number} size - 爆発のサイズ
        @returns {Effect} - 生成されたエフェクトオブジェクト
        """
        return Effect(x, y, EFFECT_TYPE_EXPLOSION, size, 30)
    
    @staticmethod
    def create_hit(x, y):
        """
        ヒットエフェクトを生成するファクトリメソッド
        
        @param {number} x - エフェクトのX座標
        @param {number} y - エフェクトのY座標
        @returns {Effect} - 生成されたエフェクトオブジェクト
        """
        return Effect(x, y, EFFECT_TYPE_HIT, 5, 15)
    
    @staticmethod
    def create_spawn(x, y, size=15):
        """
        出現エフェクトを生成するファクトリメソッド
        
        @param {number} x - エフェクトのX座標
        @param {number} y - エフェクトのY座標
        @param {number} size - 出現エフェクトのサイズ
        @returns {Effect} - 生成されたエフェクトオブジェクト
        """
        return Effect(x, y, EFFECT_TYPE_SPAWN, size, 20)
    
    @staticmethod
    def create_bomb(x, y):
        """
        ボムエフェクトを生成するファクトリメソッド
        
        @param {number} x - エフェクトのX座標
        @param {number} y - エフェクトのY座標
        @returns {Effect} - 生成されたエフェクトオブジェクト
        """
        return Effect(x, y, EFFECT_TYPE_BOMB, 0, 60) 