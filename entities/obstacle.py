"""
障害物クラスモジュール

ゲーム内の障害物の動作と描画を担当するクラスを定義します。
"""

import pyxel
import random
import math

class Obstacle:
    """
    障害物クラス
    
    プレイヤーの妨げとなる障害物の動作、描画を担当します。
    """
    def __init__(self, x, y, width, height, speed, obstacle_type=0):
        """
        障害物を初期化します。
        
        @param {number} x - 障害物のX座標
        @param {number} y - 障害物のY座標
        @param {number} width - 障害物の幅
        @param {number} height - 障害物の高さ
        @param {number} speed - 障害物の落下速度
        @param {number} obstacle_type - 障害物の種類（0:通常、1:回転、2:ジグザグ）
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.type = obstacle_type
        self.angle = 0  # 回転角度（タイプ1の場合に使用）
        self.direction = 1  # 横移動の向き（タイプ2の場合に使用）
        self.sin_offset = random.uniform(0, math.pi * 2)  # サイン波のオフセット
        self.health = 3 if obstacle_type == 2 else 1  # 障害物の耐久度（タイプ2は耐久力が高い）
        
    def update(self):
        """
        障害物の状態を更新します。
        
        @returns {boolean} - 障害物が画面外に出たらTrue
        """
        # タイプに応じた動作
        if self.type == 0:
            # タイプ0: 単純な下方向への移動
            self.y += self.speed
        elif self.type == 1:
            # タイプ1: 回転しながら下に落ちる
            self.y += self.speed
            self.angle += 0.1  # 回転速度
            # 左右に少し揺れる
            self.x += math.sin(self.angle + self.sin_offset) * 0.5
        elif self.type == 2:
            # タイプ2: ジグザグに動く
            self.y += self.speed
            # 左右に大きく動く
            self.x += math.sin(pyxel.frame_count / 10 + self.sin_offset) * 2 * self.direction
            
            # 画面端に達したら向きを変える
            if self.x < 0:
                self.x = 0
                self.direction = 1
            elif self.x > pyxel.width - self.width:
                self.x = pyxel.width - self.width
                self.direction = -1
                
        # 画面外に出たら削除
        return self.y > pyxel.height

    def draw(self):
        """
        障害物を描画します。
        """
        if self.type == 0:
            # タイプ0: 単純な四角形
            pyxel.rect(self.x, self.y, self.width, self.height, 5)
        elif self.type == 1:
            # タイプ1: 回転する障害物（菱形で表現）
            center_x = self.x + self.width / 2
            center_y = self.y + self.height / 2
            size = self.width / 2
            
            # 回転する菱形（簡易表現）
            offset = math.sin(self.angle) * 3
            pyxel.tri(
                center_x, center_y - size,
                center_x + size, center_y,
                center_x, center_y + size,
                9  # 緑色
            )
            pyxel.tri(
                center_x, center_y - size,
                center_x - size, center_y,
                center_x, center_y + size,
                9  # 緑色
            )
        elif self.type == 2:
            # タイプ2: 耐久力の高い障害物
            pyxel.rect(self.x, self.y, self.width, self.height, 10)  # 青色
            
            # 耐久度に応じた模様
            for i in range(self.health):
                margin = 2
                inner_width = self.width - margin * 2
                segment = inner_width / 3
                pyxel.rect(
                    self.x + margin + segment * i,
                    self.y + margin,
                    segment,
                    self.height - margin * 2,
                    11  # 紫色
                )
                
    def get_hit(self, damage=1):
        """
        障害物がダメージを受けたときの処理を行います。
        
        @param {number} damage - 受けるダメージ量
        @returns {boolean} - 破壊されたらTrue
        """
        self.health -= damage
        if self.health <= 0:
            return True
        return False 