from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random, math

app = Ursina()

# Sesler
try:
    music = Audio('ocania.mp3', loop=True, autoplay=True)
    music2 = Audio('bird.mp3', loop=True, autoplay=True)
    exp_sound = Audio('exp.mp3', loop=False, autoplay=False)
    boom_sound = Audio('boom.mp3', loop=False, autoplay=False)
    fire_sound = Audio('fire.mp3', loop=False, autoplay=False)
    select_sound = Audio('select.mp3', loop=False, autoplay=False)
    attack_sound = Audio('attack.mp3', loop=False, autoplay=False)
except:
    print("Ses dosyaları bulunamadı.")

# Oyuncu
player = FirstPersonController()
player.position = (5,3,5)
spawn_point = Vec3(5,3,5)
player_health = 3

# UI
health_text = Text(text=f"❤️ {player_health}", position=(-0.85,0.4), scale=1.5, color=color.red)
chaos_timer = 100
chaos_text = Text(text=f"CHAOS EVENT: {chaos_timer}", position=(-0.85,0.45), scale=1.5, color=color.orange)
sky = Sky(texture='sky.png')

# Envanter ve kılıç
current_item = 'grass'
all_blocks = []
lava_balls = []
enemies = []

grass_btn = Button(text='Grass', color=color.green, scale=(.1,.1), position=(-.45,-.45))
stone_btn = Button(text='Stone', color=color.gray, scale=(.1,.1), position=(-.3,-.45))
wood_btn  = Button(text='Wood', color=color.orange, scale=(.1,.1), position=(-.15,-.45))
iron_btn  = Button(text='Iron', color=color.light_gray, scale=(.1,.1), position=(0,-.45))
obs_btn   = Button(text='Obsidian', color=color.rgb(50,0,70), scale=(.1,.1), position=(.15,-.45))
sword_btn = Button(text='Sword', color=color.azure, scale=(.1,.1), position=(.3,-.45))

sword_icon = Entity(parent=camera.ui, model='quad', texture='sword.png', scale=(.15,.15), position=(.7,-.35), enabled=False)

def update_inventory_ui():
    grass_btn.color = color.lime if current_item=='grass' else color.green
    stone_btn.color = color.light_gray if current_item=='stone' else color.gray
    wood_btn.color  = color.yellow if current_item=='wood' else color.orange
    iron_btn.color  = color.white if current_item=='iron' else color.light_gray
    obs_btn.color   = color.rgb(120,0,160) if current_item=='obsidian' else color.rgb(50,0,70)
    sword_btn.color = color.azure if current_item=='sword' else color.gray
    sword_icon.enabled = current_item=='sword'

update_inventory_ui()

# Mesafe
def dist(a,b): return math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2 + (a.z-b.z)**2)

# Patlama
def explosion_effect(position):
    for i in range(15):
        e = Entity(model='sphere', color=color.orange, scale=0.2, position=position)
        e.animate_position(e.position + Vec3(random.uniform(-1,1), random.uniform(0,1), random.uniform(-1,1)),
                           duration=0.5, curve=curve.out_quad)
        e.animate_scale(0, duration=0.5)
        destroy(e, delay=0.5)

def camera_shake(intensity=0.15,duration=0.3):
    original_pos = camera.position
    for i in range(10):
        invoke(lambda: setattr(camera,'position', original_pos + Vec3(random.uniform(-intensity,intensity),
                                                                     random.uniform(-intensity,intensity),0)), delay=i*0.03)
    invoke(lambda:setattr(camera,'position',original_pos), delay=duration)

# Blok ve su
class Block(Button):
    def __init__(self, position=(0,0,0), block_type='grass'):
        self.block_type = block_type
        collider_flag = True
        if block_type=='grass': color_val=color.green
        elif block_type=='stone': color_val=color.gray
        elif block_type=='wood': color_val=color.orange
        elif block_type=='iron': color_val=color.rgb(200,200,200)
        elif block_type=='obsidian': color_val=color.rgb(40,0,80)
        elif block_type=='water': color_val=color.azure; collider_flag=False
        else: color_val=color.white
        super().__init__(parent=scene, position=position, model='cube', color=color_val,
                         origin_y=0.5, collider='box' if collider_flag else None)
        all_blocks.append(self)

    def input(self,key):
        if self.hovered:
            if key=='left mouse down':
                if self in all_blocks: all_blocks.remove(self)
                destroy(self)
            if key=='right mouse down' and current_item!='sword':
                place_block(self.position + mouse.normal)

class WaterBlock(Block):
    def __init__(self, position):
        super().__init__(position=position, block_type='water')
        self.flow_timer=0

    def update(self):
        self.flow_timer+=time.dt
        t=math.sin(time.time()*3 + self.position.x + self.position.z)*0.1
        self.color=color.azure.tint(t)

def snap_to_grid(pos): return Vec3(round(pos.x), round(pos.y), round(pos.z))
def place_block(position): Block(position=snap_to_grid(position), block_type=current_item)

# Alan 10x10
for x in range(10):
    for z in range(10):
        Block(position=(x,0,z), block_type='stone')
        WaterBlock(position=(x,1,z))
        Block(position=(x,2,z), block_type='grass')

# Klavye
def input(key):
    global current_item
    if key in ['1','2','3','4','5','6']:
        try: select_sound.play()
        except: pass
    if key=='1': current_item='grass'
    elif key=='2': current_item='stone'
    elif key=='3': current_item='wood'
    elif key=='4': current_item='iron'
    elif key=='5': current_item='obsidian'
    elif key=='6': current_item='sword'
    elif key=='escape': application.quit()
    update_inventory_ui()

# Patlama
def explode(position,radius=2):
    try: boom_sound.play()
    except: pass
    explosion_effect(position)
    camera_shake()
    affected_blocks = [b for b in all_blocks if dist(b.position, position)<=radius]
    for b in affected_blocks:
        if b in all_blocks: all_blocks.remove(b)
        destroy(b)

# Lava Topu
class LavaBall(Entity):
    def __init__(self,start_pos,target):
        super().__init__(model='sphere',color=color.red,scale=0.8,position=start_pos,collider='sphere')
        self.target=target; self.speed=2
        try: fire_sound.play()
        except: pass
    def update(self):
        direction=(self.target.position - self.position).normalized()
        self.position += direction*self.speed*time.dt
        if dist(self.position,self.target.position)<1:
            print("ALEV TOPLU TARAFINDAN PATLATILDINIZ")
            application.quit()
        for b in all_blocks.copy():
            if dist(self.position,b.position)<1:
                explode(self.position, radius=2)
                if self in lava_balls: lava_balls.remove(self)
                destroy(self)
                return

# Düşman
class Enemy(Entity):
    def __init__(self,position):
        super().__init__(model='cube',color=color.dark_gray,scale=(1,2,1),position=position,collider='box')
        self.speed=1
        self.attack_cooldown=0
    def safe_update(self):
        global player_health
        direction=(player.position-self.position).normalized()
        self.position+=direction*self.speed*time.dt
        if dist(self.position,player.position)<1.5:
            self.attack_cooldown+=time.dt
            if self.attack_cooldown>=10:
                player_health-=1
                self.attack_cooldown=0
                health_text.text=f"❤️ {player_health}"
                print("Düşman sana vurdu!")
                if player_health<=0: print("ÖLDÜN!"); application.quit()
        else: self.attack_cooldown=0

# Kılıç
def attack():
    if current_item!='sword': return
    try: attack_sound.play()
    except: pass
    for enemy in enemies.copy():
        if dist(enemy.position,player.position)<2:
            enemies.remove(enemy)
            destroy(enemy)
            print("Düşman öldürüldü!")

# Gece/gündüz
is_night=False
def update_sky_texture():
    sky.texture='night.png' if is_night else 'sky.png'

# CHAOS EVENT
def chaos_event():
    global chaos_timer,is_night
    try: exp_sound.play()
    except: pass
    for _ in range(3):
        spawn_pos=player.position+Vec3(random.randint(-10,10),random.randint(10,15),random.randint(-10,10))
        lava_balls.append(LavaBall(start_pos=spawn_pos,target=player))
    is_night=not is_night
    update_sky_texture()
    chaos_timer=100
    invoke(chaos_event,delay=100)

# Düşman spawn
def spawn_enemy():
    pos=player.position+Vec3(random.randint(-10,10),1,random.randint(-10,10))
    enemies.append(Enemy(position=pos))
    invoke(spawn_enemy,delay=30)

# Update
def update():
    global chaos_timer
    if player.y<-10:
        player.position=spawn_point
        player.velocity=Vec3(0,0,0)
    chaos_timer-=time.dt
    chaos_text.text=f"CHAOS EVENT: {int(chaos_timer)}"
    if held_keys['left mouse']: attack()
    for lb in lava_balls.copy(): lb.update()
    for e in enemies.copy(): e.safe_update()
    for b in all_blocks:
        if isinstance(b,WaterBlock): b.update()

Sky(texture='sky.png')
invoke(chaos_event,delay=100)
invoke(spawn_enemy,delay=5)
app.run()
