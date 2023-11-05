import pygame
import random

from typing import Callable
from pygame import Vector2, Rect, Color, Surface


pygame.init()




class Signal:

    def __init__(self):
        self.handlers = []
    

    def connect(self, handler: callable) -> None:
        self.handlers.append(handler)

    def disconnect(self, handler: callable) -> None:
        self.handlers.remove(handler)

    def disconnect_all(self) -> None:
        self.handlers.clear()
    
    def emit(self, *args, **kwargs) -> None:
        for handler in self.handlers:
            handler(*args, **kwargs)


class Buff:

    def __init__(self):
        self.name = "Buff"
        self.desc = ""

    def __str__(self) -> str:
        return f"{self.name}({self.desc})"

    def use(self, player: "Player") -> None:
        pass


class HealthBuff(Buff):

    def __init__(self, value: int):
        super().__init__()
        self.name = "勇往直前"
        self.desc = f"恢复{value}点生命值."
        self.value = value

    def use(self, player: "Player") -> None:
        player.health += self.value


class BulletDamage(Buff):

    def __init__(self, value: int):
        super().__init__()
        self.name = "血脉觉醒"
        self.desc = f"每颗子弹增加{value}点伤害."
        self.value = value

    def use(self, player: "Player") -> None:
        player.gun.bullet_damage += self.value


class BulletSpeed(Buff):

    def __init__(self, value: int):
        super().__init__()
        self.name = "速战速决"
        self.desc = f"子弹速度增加{value}点."
        self.value = value

    def use(self, player: "Player") -> None:
        player.gun.bullet_speed += self.value


class FireRateBuff(Buff):

    def __init__(self, value: int):
        super().__init__()
        self.name = "唯快不破"
        self.desc = f"枪的射速增加{value}点."
        self.value = value

    def use(self, player: "Player") -> None:
        player.gun.firing_rate += self.value


class FireBulletCountBuff(Buff):

    def __init__(self, value: int):
        super().__init__()
        self.name = "火力覆盖"
        self.desc = f"发射子弹的颗数增加{value}颗."
        self.value = value

    def use(self, player: "Player") -> None:
        player.gun.fire_bullet_count += self.value


class BulletKnockbackForce(Buff):

    def __init__(self, value: int):
        super().__init__()
        self.name = "大力出奇迹"
        self.desc = f"击退力度增加{value}点."
        self.value = value

    def use(self, player: "Player") -> None:
        player.gun.bullet_knockback_force += self.value


Buffs = [
    (HealthBuff, 5, 15),
    (BulletDamage, 1, 30),
    (BulletSpeed, 20, 100),
    (FireRateBuff, 1, 2),
    (FireBulletCountBuff, 1, 2),
    (BulletKnockbackForce, 1, 5)
]


class Node2D:

    def __init__(self, parent: "Node2D", pos: Vector2, size: Vector2, z_index: int = 0):
        self.parent = parent
        self.pos = pos
        self.size = size
        self.collision_rect = Rect(pos, size)
        self.z_index = z_index
        self.visible = True
        self.can_paused = True
        self.children = []
        self.can_collide = False
        self.has_collided_signal = Signal()

        self.set_parent(parent)

    
    def update(self, delta: float) -> None:
        pass


    def draw(self, surface: Surface) -> None:
        if not self.visible: return

    def set_parent(self, parent: "Node2D") -> None:
        self.parent = parent
        if parent is None:
            return
        if not self in parent.children:
            parent.children.append(self)

    
    def add_child(self, child: "Node2D") -> None:
        self.children.append(child)
        child.set_parent(self)


    def remove_child(self, child: "Node2D") -> None:
        if child not in self.children:
            return
        self.children.remove(child)
        child.set_parent(None)


    def remove_all_children(self) -> None:
        for child in self.children[:]:
            self.children.remove(child)
            child.set_parent(None)

    
    def remove(self) -> None:
        if self.parent is None:
            return
        self.parent.remove_child(self)
        self.parent = None


    def get_all_children(self) -> list:
        all_children = []
        for child in self.children:
            all_children.append(child)
            all_children.extend(child.get_all_children())
        return all_children
    

    def get_root(self) -> "Root":
        if isinstance(self, Root):
            return self
        
        if isinstance(self.parent, Root):
            return self.parent

        return self.parent.get_root()


    def get_rect(self) -> Rect:
        return Rect(self.pos, self.size)
    

    def add_in_group(self, name: str) -> None:
        root = self.get_root()
        if root is None: return
        group = root.groups.get(name)
        if group is None:
            group = []
            root.groups[name] = group
        group.append(self)



class Root(Node2D):

    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance


    def __init__(self):
        super().__init__(None, Vector2(0, 0), Vector2(pygame.display.get_surface().get_size()))
        self.groups = {}
        self.delta = 0.0
        self.clear_color = Color(0, 0, 0)
        self.mouse_pos = Vector2(0, 0)

        self.__pause_time = 0
        self.__pause_duration = 0
        self.__is_paused = False


    def update(self, delta: float) -> None:
        self.delta = delta
        self.mouse_pos = pygame.mouse.get_pos()


    def get_nodes_in_group(self, name: str) -> list:
        group = self.groups.get(name)
        if group is None:
            return []
        return group

    
    def get_first_node_in_group(self, name: str) -> Node2D:
        group = self.groups.get(name)
        if group is None:
            return None
        return group[0]


    def pause(self, value: bool) -> None:
        self.__is_paused = value
        if value:
            self.__pause_time = pygame.time.get_ticks()
        else:
            self.__pause_duration += pygame.time.get_ticks() - self.__pause_time


    def is_paused(self) -> bool:
        return self.__is_paused

    
    def get_ticks(self, offset: int = 0) -> int:
        return pygame.time.get_ticks() - self.__pause_duration + offset



class Sprite2D(Node2D):

    def __init__(self, parent: Node2D, pos: Vector2, image: Surface):
        super().__init__(parent, pos, Vector2(image.get_size()))
        self.image = image
        self.size = Vector2(image.get_size())
    
    def draw(self, surface: Surface) -> None:
        super().draw(surface)
        surface.blit(self.image, self.pos)


class HealthBar(Sprite2D):

    def __init__(self, parent: Node2D, max_health: int, pos: Vector2, size: Vector2, border: int = 1):
        super().__init__(parent, pos, Surface(size))
        self.max_health = max_health
        self.health = max_health
        self.border = border
        self.border_color = Color(255, 255, 255)
        self.value_color = Color(255, 0, 0)
        self.z_index = 5
        self.image.set_colorkey((0, 0, 0))

    def draw(self, surface: Surface) -> None:
        self.image.fill((0, 0, 0))
        pygame.draw.rect(self.image, self.border_color, (0, 0, self.size.x, self.size.y), self.border)
        pygame.draw.rect(self.image, self.value_color, (self.border, self.border, (self.size.x - self.border * 2) * self.health * 1.0 / self.max_health, self.size.y - self.border * 2))
        super().draw(surface)


class Bullet(Sprite2D):

    def __init__(self, parent: Node2D, pos: Vector2, direction: Vector2):
        super().__init__(parent, pos, Surface((10, 10)))
        self.speed = 800
        self.damage = 5
        self.knockback_force = 5
        self.can_penetrate = False
        self.direction = direction
        self.z_index = 2
        self.image.set_colorkey((0, 0, 0))
        self.can_collide = True
        self.pos -= self.size / 2


    def update(self, delta: float) -> None:
        self.pos += self.speed * self.direction * delta
        self.collision_rect.topleft = self.pos

        rect = pygame.display.get_surface().get_rect()
        if self.pos.x < 0 or self.pos.x > rect.width or self.pos.y < 0 or self.pos.y > rect.height:
            self.remove()

    
    def draw(self, surface: Surface) -> None:
        pygame.draw.circle(self.image, (0, 255, 0), self.size / 2, self.size.x / 2)
        super().draw(surface)


class Gun(Node2D):

    def __init__(self, parent: Node2D):
        super().__init__(parent, Vector2(parent.get_rect().center), Vector2())
        self.z_index = 3
        
        self.__laste_fire_time = 0
        self.firing_rate = 3
        self.bullet_damage = 5
        self.bullet_speed = 800
        self.bullet_knockback_force = 5
        self.bullet_can_penetrate = False
        self.fire_bullet_count = 1

    
    def _create_bullet(self, direction: Vector2) -> None:
        bullet = Bullet(self, self.pos.copy(), direction)
        bullet.can_penetrate = self.bullet_can_penetrate
        bullet.damage = self.bullet_damage
        bullet.speed = self.bullet_speed
        bullet.knockback_force = self.bullet_knockback_force

    
    def _create_multiple_bullets(self, count: int, base_direction: Vector2, rotate_angle: float) -> None:
        for i in range(1, count + 1):
            angle = base_direction
            if self.fire_bullet_count % 2 == 0:
                if i == 1:
                    angle = base_direction.rotate(rotate_angle / 2)
                else:
                    angle = base_direction.rotate((i-1) * rotate_angle + rotate_angle / 2)
            else:
                angle = base_direction.rotate(i * rotate_angle)

            self._create_bullet(angle)

    
    def fire(self, direction: Vector2) -> None:
        if self.get_root().get_ticks() - self.__laste_fire_time < 1000.0 / self.firing_rate:
            return

        half = self.fire_bullet_count // 2
        self._create_multiple_bullets(half, direction, 5)

        if not self.fire_bullet_count % 2 == 0:
            self._create_bullet(direction)

        self._create_multiple_bullets(half, direction, -5)

        self.__laste_fire_time = self.get_root().get_ticks()
        


class Player(Sprite2D):

    def __init__(self, parent: Node2D, pos: Vector2):
        super().__init__(parent, pos, Surface(Vector2(60, 60)))
        self.speed = 500
        self.z_index = 1
        self.can_collide = True
        self.image.fill((255, 0, 0))
        self.limit_rect = Rect(pygame.display.get_surface().get_rect())
        self.died_signal = Signal()

        self.max_health = 100
        self.health = self.max_health
        self.score = 0
        self.kill_count = 0

        self.add_in_group("player")

        self.gun = Gun(self)
        self.gun.bullet_damage = 50
        self.gun.firing_rate = 5
        self.gun.bullet_speed = 650
        self.gun.bullet_knockback_force = 5
        self.gun.fire_bullet_count = 1
        # self.gun.bullet_can_penetrate = True

        self._init_data = self._get_init_data()

    
    def __str__(self) -> str:
        return f"""Player(
            bullet_damage: {self.gun.bullet_damage},
            firing_rate: {self.gun.firing_rate},
            bullet_speed: {self.gun.bullet_speed},
            bullet_knockback_force: {self.gun.bullet_knockback_force},
            fire_bullet_count: {self.gun.fire_bullet_count},
            health: {self.health},
        )"""


    def update(self, delta: float) -> None:
        keys = pygame.key.get_pressed()
        direction = Vector2()
        if keys[pygame.K_w]:
            direction.y = -1
        if keys[pygame.K_s]:
            direction.y = 1
        if keys[pygame.K_a]:
            direction.x = -1
        if keys[pygame.K_d]:
            direction.x = 1
        
        pos = self.pos
        direction = direction.normalize() if direction.length() != 0 else direction
        pos += direction * self.speed * delta

        if pos.x < self.limit_rect.left:
            pos.x = self.limit_rect.left
        if pos.x > self.limit_rect.right - self.size.x:
            pos.x = self.limit_rect.right - self.size.x
        if pos.y < self.limit_rect.top:
            pos.y = self.limit_rect.top
        if pos.y > self.limit_rect.bottom - self.size.y:
            pos.y = self.limit_rect.bottom - self.size.y

        self.pos = pos
        self.collision_rect.topleft = self.pos
        self.gun.pos = Vector2(self.get_rect().center)

        shoot_direction = Vector2(pygame.mouse.get_pos()) - self.get_rect().center
        shoot_direction = shoot_direction.normalize() if shoot_direction.length()!= 0 else shoot_direction
        # if pygame.mouse.get_pressed()[0]:
        self.gun.fire(shoot_direction)

    def set_health(self, health: int) -> None:
        self.health = pygame.math.clamp(health, 0, self.max_health)
        if self.health <= 0:
            self.died_signal.emit()

    def _get_init_data(self) -> dict:
        return {
            "pos": self.pos.copy(),
            "speed": self.speed,
            "health": self.health,
            "score": self.score,
            "kill_count": self.kill_count,
            "max_health": self.max_health,
            "bullet_can_penetrate": self.gun.bullet_can_penetrate,
            "bullet_damage": self.gun.bullet_damage,
            "firing_rate": self.gun.firing_rate,
            "bullet_speed": self.gun.bullet_speed,
            "bullet_knockback_force": self.gun.bullet_knockback_force,
            "fire_bullet_count": self.gun.fire_bullet_count,
        }

    def restore_init_data(self) -> None:
        self.pos = self._init_data["pos"]
        self.speed = self._init_data["speed"]
        self.health = self._init_data["health"]
        self.score = self._init_data["score"]
        self.kill_count = self._init_data["kill_count"]
        self.max_health = self._init_data["max_health"]
        self.gun.bullet_can_penetrate = self._init_data["bullet_can_penetrate"]
        self.gun.bullet_damage = self._init_data["bullet_damage"]
        self.gun.firing_rate = self._init_data["firing_rate"]
        self.gun.bullet_speed = self._init_data["bullet_speed"]
        self.gun.bullet_knockback_force = self._init_data["bullet_knockback_force"]
        self.gun.fire_bullet_count = self._init_data["fire_bullet_count"]


class Cursor(Sprite2D):

    def __init__(self, parent: Node2D):
        super().__init__(parent, Vector2(0, 0), Surface((12, 12)))
        self.z_index = 9999
        self.thickness = 2
        self.color = Color((0, 255, 0))
        self.image.set_colorkey((0, 0, 0))
        self.can_paused = False
        pygame.mouse.set_visible(False)


    def update(self, delta: float) -> None:
        self.pos = pygame.mouse.get_pos()

    def draw(self, surface: Surface) -> None:
        pygame.draw.line(self.image, self.color, Vector2(self.size.x / 2 - self.thickness / 2, 0), Vector2(self.size.x / 2 - self.thickness / 2, self.size.y), self.thickness)
        pygame.draw.line(self.image, self.color, Vector2(0, self.size.y / 2 - self.thickness / 2), Vector2(self.size.x, self.size.y / 2 - self.thickness / 2), self.thickness)
        super().draw(surface)


class Enemy(Sprite2D):

    init_data = {}

    def __init__(self, parent: Node2D, pos: Vector2):
        super().__init__(parent, pos, Surface((30, 30)))
        self.speed = 80
        self.z_index = 0
        self.image.fill((255, 255, 255))
        self.can_collide = True

        self.player = self.get_root().get_first_node_in_group("player")

        self.max_health = 500
        self.health = self.max_health

        Enemy.init_data = self._get_init_data()

        self.health_bar = HealthBar(self, self.max_health, Vector2(self.pos.x, self.pos.y - 15), Vector2(self.size.x, 8), 2)

        self.has_collided_signal.connect(self._on_has_collided_signal)

    def update(self, delta: float) -> None:
        self.collision_rect.topleft = self.pos
        self.health_bar.pos = Vector2(self.pos.x, self.pos.y - 15)

        direction = Vector2(self.player.get_rect().center) - Vector2(self.get_rect().center)
        if direction.length()!= 0:
            direction = direction.normalize()
        self.pos += direction * self.speed * delta

    
    def draw(self, surface: Surface) -> None:
        pygame.draw.circle(self.image, (255, 0, 0), self.size / 2, 7.5)
        super().draw(surface)

    def _get_init_data(self) -> dict:
        return {
            "speed": self.speed,
            "health": self.health,
            "max_health": self.max_health,
        }
    

    def _on_has_collided_signal(self, node: Node2D) -> None:
        if isinstance(node, Bullet):
            self.health -= node.damage
            self.health_bar.health = self.health
            self.pos += node.direction * node.knockback_force
            if self.health <= 0:
                self.player.score += 5
                self.player.kill_count += 1
                self.remove()
            if not node.can_penetrate:
                node.remove()

        if isinstance(node, Player):
            self.player.score -= 10
            self.player.set_health(self.player.health - 10)
            self.player.kill_count += 1
            self.remove()


class Lable(Node2D):

    def __init__(self, parent: Node2D, pos: Vector2, text: str = ""):
        super().__init__(parent, pos, Vector2())  
        self.font = pygame.font.SysFont("SimHei", 30)
        self.font_color = Color(255, 255, 255)
        self.text_surfaces = []
        self.__text = text
        self.set_text(text)


    def update(self, delta: float) -> None:
        self.text_surfaces.clear()
        lines = self.__text.split("\n")
        line_height = self.font.get_linesize()
        y = self.pos.y
        max_width = 0
        for line in lines:
            text_surface = self.font.render(line, True, self.font_color)
            self.text_surfaces.append((text_surface, Vector2(self.pos.x, y)))
            y += line_height
            if text_surface.get_width() > max_width:
                max_width = text_surface.get_width()

        self.size = Vector2(max_width, len(lines) * line_height)


    def draw(self, surface: Surface) -> None:
        for text_surface, pos in self.text_surfaces:
            surface.blit(text_surface, pos)


    def set_text(self, text: str) -> None:
        self.__text = text
        # self.text_surfaces.clear()
        # lines = self.__text.split("\n")
        # line_height = self.font.get_linesize()
        # y = self.pos.y
        # max_width = 0
        # for line in lines:
        #     text_surface = self.font.render(line, True, self.font_color)
        #     self.text_surfaces.append((text_surface, Vector2(self.pos.x, y)))
        #     y += line_height
        #     if text_surface.get_width() > max_width:
        #         max_width = text_surface.get_width()

        # self.size = Vector2(max_width, len(lines) * line_height)

    def get_text(self) -> str:
        return self.__text
        


class Button(Node2D):

    def __init__(self, parent: Node2D, pos: Vector2,  text: str):
        super().__init__(parent, pos, Vector2())
        self.padding = Vector2(10)
        self.is_pressed = False
        self.text_lbl = Lable(self, pos + self.padding, text)
        self.bg_color = Color(0, 0, 0)
        self.border_color = Color(255, 255, 255)
        self.border_width = 3
        self.hot_keys = []
        self.hot_key_pressed = False
        self.set_text(text)
        self.pressed_singal = Signal()

    def update(self, delta: float) -> None:
        self.size = Vector2(self.text_lbl.size) + self.padding * 2
        self.text_lbl.pos = self.pos + self.padding 
        self.text_lbl.z_index = self.z_index
        self.text_lbl.can_paused = self.can_paused
        self.text_lbl.visible = self.visible

        if self.visible:
            if pygame.mouse.get_pressed()[0] and self.get_rect().collidepoint(pygame.mouse.get_pos()) and not self.is_pressed:
                self.pressed_singal.emit()
                self.is_pressed = True
            if not pygame.mouse.get_pressed()[0]:
                self.is_pressed = False

        keys = pygame.key.get_pressed()
        for key in self.hot_keys:
            if keys[key]:
                if self.hot_key_pressed:
                    break
                self.pressed_singal.emit()
                self.hot_key_pressed = True
                break
            else:
                self.hot_key_pressed = False

        
    def draw(self, surface: Surface) -> None:
        pygame.draw.rect(surface, self.bg_color, Rect(self.pos.x, self.pos.y, self.size.x, self.size.y))
        pygame.draw.rect(surface, self.border_color, Rect(self.pos.x, self.pos.y, self.size.x, self.size.y), self.border_width)


    def set_text(self, text: str) -> None:
        self.text_lbl.set_text(text)
        self.size = Vector2(self.text_lbl.size) + self.padding * 2

    
    def get_text(self) -> str:
        return self.text_lbl.get_text()
   


class BuffPanel(Sprite2D):

    def __init__(self, parent: Node2D):
        super().__init__(parent, Vector2(0, 0), Surface(pygame.display.get_surface().get_size(), pygame.SRCALPHA))
        self.image.fill(Color(0, 0, 0, 100))

        self.buff_btns = []
        self.buff_btn1 = Button(self, Vector2(10, 10), "buff1")
        self.buff_btn2 = Button(self, Vector2(120, 10), "buff2")
        self.buff_btn3 = Button(self, Vector2(230, 10), "buff3")
        self.buff_btns.append(self.buff_btn1)
        self.buff_btns.append(self.buff_btn2)
        self.buff_btns.append(self.buff_btn3)

        self.player = self.get_root().get_first_node_in_group("player")

        self.visible = False
        self.can_paused = False
        for btn in self.buff_btns:
            btn.can_paused = self.can_paused


    def update(self, delta: float) -> None:
        width = 0
        max_height = 0
        for btn in self.buff_btns:
            btn.z_index = self.z_index
            width += btn.size.x
            if btn.size.y > max_height:
                max_height = btn.size.y
        
        pos = Vector2((self.size.x - width - 2 * 20) / 2, (self.size.y - max_height) / 2)
        for btn in self.buff_btns:
            btn.pos = pos.copy()
            pos.x += btn.size.x + 20
            btn.visible = self.visible
        

    def draw(self, surface: Surface) -> None:
        super().draw(surface)

    
    def _on_buff_btn_pressed(self, buff: Buff) -> None:
            buff.use(self.player)
            self.visible = False
            self.get_root().pause(not self.get_root().is_paused())

    def _bind_buff(self, btn: Button) -> None:
        b = random.choice(Buffs)
        buff = b[0](random.randint(b[1], b[2]))
        btn.set_text(f"{buff.name}\n{buff.desc}")
        btn.pressed_singal.disconnect_all()
        btn.pressed_singal.connect(lambda: self._on_buff_btn_pressed(buff))

    def display(self) -> None:
        for btn in self.buff_btns:
            self._bind_buff(btn)
            
        self.visible = True


class GameOverPanel(Sprite2D):

    def __init__(self, parent: Node2D):
        super().__init__(parent, Vector2(0, 0), Surface(pygame.display.get_surface().get_size(), pygame.SRCALPHA))
        self.image.fill(Color(0, 0, 0, 100))
        self.z_index = 99
        self.can_paused = False
        self.visible = False

        self.lbl = Lable(self, Vector2(), "游戏结束")
        self.lbl.font_color = Color(255, 0, 0)
        self.lbl.font = pygame.font.SysFont("SimHei", 50)
        self.lbl.can_paused = False

        self.restart_bnt = Button(self, Vector2(10, 10), "重新开始")
        self.restart_bnt.can_paused = False

    
    def update(self, delta: float) -> None:
        self.lbl.visible = self.visible
        self.restart_bnt.visible = self.visible

        self.lbl.z_index = self.z_index
        self.restart_bnt.z_index = self.z_index

        self.lbl.pos = (self.size - self.lbl.size) / 2
        self.lbl.pos.y -= 100
        self.restart_bnt.pos = (self.size - self.restart_bnt.size) / 2
        self.restart_bnt.pos.y += self.lbl.size.y 

        
        

class TopUI(Node2D):

    def __init__(self, parent: Node2D):
        super().__init__(parent, Vector2(0, 0), Vector2(pygame.display.get_surface().get_size()))
        self.z_index = 99
        self.add_in_group("top_ui")

        self.player = self.get_root().get_first_node_in_group("player")

        self.player_health_bar = HealthBar(self, self.player.max_health, Vector2(), Vector2(400, 20), 3)
        self.player_health_bar.z_index = self.z_index
        self.player_health_bar.pos.x = (self.size.x - self.player_health_bar.size.x) / 2
        self.player_health_bar.pos.y = self.size.y - self.player_health_bar.size.y - 10

        self.player_health_lbl = Lable(self, Vector2(10, 10))
        self.player_health_lbl.z_index = self.z_index
        self.player_health_lbl.pos.y = self.player_health_bar.pos.y - self.player_health_lbl.size.y - 5

        self.score_lbl = Lable(self, Vector2(10, 10))
        self.score_lbl.z_index = self.z_index

        self.timer_lbl = Lable(self, Vector2(10, 10))
        self.timer_lbl.z_index = self.z_index

        self.kill_count_lbl = Lable(self, Vector2(10, 10))
        self.kill_count_lbl.z_index = self.z_index

        self.buff_panel = BuffPanel(self)
        self.buff_panel.z_index = self.z_index + 1
        self.buff_panel.visible = False

        pause_btn = Button(self, Vector2(10, 10), "暂停")
        pause_btn.visible = False
        pause_btn.can_paused = False
        pause_btn.hot_keys.append(pygame.K_ESCAPE)
        def _on_pause_btn_pressed():
            if self.over_panel.visible: return
            if self.buff_panel.visible: return
            self.get_root().pause(not self.get_root().is_paused())
        pause_btn.pressed_singal.connect(_on_pause_btn_pressed)

        self.over_panel = GameOverPanel(self)
        self.over_panel.z_index = self.z_index + 1
        
    
    def update(self, delta: float) -> None:
        self.player_health_bar.health = self.player.health

        lbl_text = f"{self.player.health}/{self.player.max_health}"
        self.player_health_lbl.set_text(lbl_text)
        self.player_health_lbl.pos.x = (self.size.x - self.player_health_lbl.size.x) / 2

        self.score_lbl.set_text(f"分数: {self.player.score}")

        self.timer_lbl.pos.x = (self.size.x - self.timer_lbl.size.x) / 2

        self.kill_count_lbl.pos.x = self.size.x - self.kill_count_lbl.size.x - 10
        self.kill_count_lbl.set_text(f"击杀: {self.player.kill_count}")
       

    def _convert_time(self, time: int) -> str:
        minutes = time // 60
        seconds = time % 60
        return f"{minutes:02}:{seconds:02}"

    
    def update_timer_lbl(self, offset: int) -> None:
        self.timer_lbl.set_text(f"{self._convert_time(int(self.get_root().get_ticks(offset) / 1000))}")
        


class MainScene(Node2D):

    def __init__(self, root: Root):
        super().__init__(root, Vector2(0, 0), Vector2(pygame.display.get_surface().get_size()))
        self.z_index = 0
        self.max_enemy_count = 10
        self.create_enemies_range = 100
        self.update_buff_time = 10
        self.enemy_health = 500
        self.enemy_speed = 80
        
        Cursor(self)
        self.player = Player(self, self.size / 2)
        self.enemies = Node2D(self, Vector2(0, 0), Vector2(0, 0))
        self.top_ui = TopUI(self)

        self.player.died_signal.connect(self.game_over)
        self.top_ui.over_panel.restart_bnt.pressed_singal.connect(self._on_game_over_btn_pressed)

        self.start_time = self.get_root().get_ticks()
        self.over_time = 0

    def update(self, delta: float) -> None:
        self.top_ui.update_timer_lbl(-self.over_time)

        if len(self.enemies.children) < self.max_enemy_count:
            pos = Vector2()
            flag = random.randrange(0, 4)
            if flag == 0:
                pos = Vector2(random.randint(0, self.size.x), random.randint(-self.create_enemies_range, 0))
            elif flag == 1:
                pos = Vector2(random.randint(0, self.size.x), random.randint(self.size.y, self.size.y + self.create_enemies_range))
            elif flag == 2:
                pos = Vector2(random.randint(-self.create_enemies_range, 0), random.randint(0, self.size.y))
            else:
                pos = Vector2(random.randint(self.size.x, self.size.x + self.create_enemies_range), random.randint(0, self.size.y))
            enemy = Enemy(self.enemies, pos)
            enemy.max_health = self.enemy_health
            enemy.health = self.enemy_health
            enemy.speed = self.enemy_speed

        for enemy in self.enemies.children[:]:
            if enemy.health <= 0:
                self.enemies.remove_child(enemy)

        if self.get_root().get_ticks() - self.start_time >= self.update_buff_time * 1000:
            if int((self.get_root().get_ticks() - self.start_time) / 1000) % self.update_buff_time == 0:
                self.get_root().pause(True)
                self.top_ui.buff_panel.display()
                self.enemy_health += 100
                self.enemy_speed += 5
                self.start_time = self.get_root().get_ticks()


    def game_over(self) -> None:
        self.get_root().pause(True)
        self.top_ui.over_panel.visible = True
        self.over_time = self.get_root().get_ticks()
    
    def _on_game_over_btn_pressed(self) -> None:
        self.get_root().pause(False)
        self.player.restore_init_data()
        self.enemy_health = Enemy.init_data["health"]
        self.enemy_speed = Enemy.init_data["speed"]
        self.enemies.remove_all_children()
        self.player.gun.remove_all_children()
        self.top_ui.over_panel.visible = False
        self.start_time = self.get_root().get_ticks()




class Game:

    def __init__(self):
        self.screen = pygame.display.set_mode((1280, 720))
        self.clock = pygame.time.Clock()
        self.running = True
        self.root = Root()
        self.root.clear_color = Color(47, 47, 47)

        MainScene(self.root)


    def run(self) -> None:
        while self.running:
            self.clock.tick(120)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            self.screen.fill(self.root.clear_color)

            delta = self.clock.get_time() / 1000
            self.root.update(delta)

            for node in sorted(self.root.get_all_children(), key=lambda node: node.z_index):
                if self.root.is_paused() and node.can_paused:
                    if node.visible:
                        node.draw(self.screen)
                    continue

                node.update(delta)
                if node.visible:
                    node.draw(self.screen)

                if isinstance(node, Bullet):
                     for other_node in self.root.get_all_children():
                        if node.parent == other_node: continue
                        if not isinstance(other_node, Enemy): continue
                        if node.collision_rect.colliderect(other_node.collision_rect):
                            other_node.has_collided_signal.emit(node)
                            if not node.can_penetrate: 
                                break
                
                if isinstance(node, Player):
                    for other_node in self.root.get_all_children():
                        if not isinstance(other_node, Enemy): continue
                        if node.collision_rect.colliderect(other_node.collision_rect):
                            other_node.has_collided_signal.emit(node)
                
            pygame.display.flip()

        pygame.quit()


Game().run()

