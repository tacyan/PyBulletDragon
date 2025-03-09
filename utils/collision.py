"""
衝突判定モジュール

ゲーム内のオブジェクト間の衝突判定を処理するユーティリティ関数を提供します。
"""

import math

def check_collision(obj1, obj2):
    """
    2つのオブジェクト間の衝突を判定します。
    
    オブジェクトの形状や属性によって適切な判定方法を選択します。
    
    @param {object} obj1 - 1つ目のオブジェクト
    @param {object} obj2 - 2つ目のオブジェクト
    @returns {boolean} - 衝突していればTrue
    """
    # ボスの弾とプレイヤーの判定
    if hasattr(obj1, 'hitbox_radius') and hasattr(obj2, 'hitbox_radius'):
        # 両方が円形当たり判定を持つ場合（弾とプレイヤーなど）
        return check_circle_collision(obj1, obj2)
    
    # プレイヤーの弾とボスの判定
    elif hasattr(obj1, 'x') and hasattr(obj1, 'y') and hasattr(obj2, 'x') and hasattr(obj2, 'width'):
        # 点と矩形の当たり判定（プレイヤーの弾とボスなど）
        if isinstance(obj1, dict) and 'x' in obj1 and 'y' in obj1:
            # obj1が弾の場合（dictでx, yを持つ）
            return check_point_rect_collision(obj1['x'], obj1['y'], obj2)
        else:
            # obj1が弾オブジェクトの場合
            return check_point_rect_collision(obj1.x, obj1.y, obj2)
    
    # それ以外の場合は矩形同士の当たり判定
    return check_rect_collision(obj1, obj2)

def check_circle_collision(obj1, obj2):
    """
    円形の当たり判定を持つ2つのオブジェクト間の衝突を判定します。
    
    @param {object} obj1 - 1つ目のオブジェクト（hitbox_radiusを持つ）
    @param {object} obj2 - 2つ目のオブジェクト（hitbox_radiusを持つ）
    @returns {boolean} - 衝突していればTrue
    """
    # オブジェクトの中心座標を計算
    if hasattr(obj1, 'width') and hasattr(obj1, 'height'):
        center1_x = obj1.x + obj1.width / 2
        center1_y = obj1.y + obj1.height / 2
    else:
        center1_x = obj1.x
        center1_y = obj1.y
        
    if hasattr(obj2, 'width') and hasattr(obj2, 'height'):
        center2_x = obj2.x + obj2.width / 2
        center2_y = obj2.y + obj2.height / 2
    else:
        center2_x = obj2.x
        center2_y = obj2.y
    
    # 2点間の距離を計算
    dx = center1_x - center2_x
    dy = center1_y - center2_y
    distance = math.sqrt(dx * dx + dy * dy)
    
    # 2つの円の半径の和より距離が小さければ衝突
    return distance < (obj1.hitbox_radius + obj2.hitbox_radius)

def check_rect_collision(obj1, obj2):
    """
    矩形の当たり判定を持つ2つのオブジェクト間の衝突を判定します。
    
    @param {object} obj1 - 1つ目のオブジェクト（x, y, width, heightを持つ）
    @param {object} obj2 - 2つ目のオブジェクト（x, y, width, heightを持つ）
    @returns {boolean} - 衝突していればTrue
    """
    return (obj1.x < obj2.x + obj2.width and
            obj1.x + obj1.width > obj2.x and
            obj1.y < obj2.y + obj2.height and
            obj1.y + obj1.height > obj2.y)

def check_point_rect_collision(point_x, point_y, rect_obj):
    """
    点と矩形の間の衝突を判定します。
    
    @param {number} point_x - 点のX座標
    @param {number} point_y - 点のY座標
    @param {object} rect_obj - 矩形オブジェクト（x, y, width, heightを持つ）
    @returns {boolean} - 衝突していればTrue
    """
    return (point_x >= rect_obj.x and 
            point_x < rect_obj.x + rect_obj.width and
            point_y >= rect_obj.y and
            point_y < rect_obj.y + rect_obj.height)

def check_bomb_collision(bomb_x, bomb_y, obj, radius):
    """
    ボムの爆発範囲内にオブジェクトがあるかを判定します。
    
    @param {number} bomb_x - ボムの中心X座標
    @param {number} bomb_y - ボムの中心Y座標
    @param {object} obj - 判定対象のオブジェクト
    @param {number} radius - ボムの爆発半径
    @returns {boolean} - 衝突していればTrue
    """
    # オブジェクトの中心座標を計算
    if hasattr(obj, 'width') and hasattr(obj, 'height'):
        obj_center_x = obj.x + obj.width / 2
        obj_center_y = obj.y + obj.height / 2
    else:
        obj_center_x = obj.x
        obj_center_y = obj.y
    
    # 2点間の距離を計算
    dx = bomb_x - obj_center_x
    dy = bomb_y - obj_center_y
    distance = math.sqrt(dx * dx + dy * dy)
    
    # ボムの爆発半径内にあるか判定
    return distance < radius 