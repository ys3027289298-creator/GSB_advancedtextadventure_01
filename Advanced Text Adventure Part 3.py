from pprint import pprint
import random
import math

class hero:
    def __init__(self, Hhealth, Hattack, Hluck, Hranged, Hdefence, Hmagic, Hname):
        self.health = Hhealth
        self.attack = Hattack
        self.luck = Hluck
        self.ranged = Hranged
        self.defence = Hdefence
        self.magic = Hmagic
        self.name = Hname

    def getHealth(self):
        return self.health
    def getAttack(self):
        return self.attack
    def getLuck(self):
        return self.luck
    def getRanged(self):
        return self.ranged
    def getDefence(self):
        return self.defence
    def getMagic(self):
        return self.magic
    def getName(self):
        return self.name

    def setHealth(self, newHealth):
        self.health = newHealth
    def setAttack(self, newAttack):
        self.attack = newAttack
    def setLuck(self, newLuck):
        self.luck = newLuck
    def setRanged(self, newRanged):
        self.ranged = newRanged
    def setDefence(self, newDefence):
        self.defence = newDefence
    def setMagic(self, newMagic):
        self.magic = newMagic
    def setName(self, newName):
        self.name = newName


class enemy:
    def __init__(self, Ehealth, Eattack, Especial, Echance, Ename):
        self.health = Ehealth
        self.attack = Eattack
        self.special = Especial
        self.chance = Echance
        self.name = Ename

    def getHealth(self):
        return self.health
    def getAttack(self):
        return self.attack
    def getSpecial (self):
        return self.special
    def getChance(self):
        return self.chance
    def getName(self):
        return self.name

    def setHealth(self, newHealth):
        self.health = newHealth
    def setAttack(self, newAttack):
        self.attack = newAttack
    def setSpecial(self, newSpecial):
        self.special = newSpecial
    def setChance(self, newChance):
        self.chance = newChance
    def setName(self, newName):
        self.name = newName



class boss (enemy):
    def __init__(self, Ehealth, Eattack, Especial, Echance, Ename, EsuperMove):
        super().__init__(Ehealth, Eattack, Especial, Echance, Ename)

        self.superMove = EsuperMove

    def getSuper(self):
        return self.superMove
    
    def setSuper(self, newSuperMove):
        self.superMove = newSuperMove

def loadLines(fileName, fallback):
    try:
        with open(fileName,"r") as file:
            lines = [line.strip() for line in file.readlines() if line.strip()]
    except IOError:
        lines = []
    if len(lines) == 0:
        return fallback
    return lines

def enemyGen(levelBoss):
    adjectives = loadLines("adjective.txt", ["Mysterious"])
    animals = loadLines("animal.txt", ["Creature"])
    adjective = adjectives[random.randint(0,len(adjectives)-1)]
    animal = animals[random.randint(0,len(animals)-1)]

    if levelBoss == False:
        health = random.randint(50,100)
        attack = random.randint(10,15)
        special = random.randint(10,20)
        chance = random.randint(1,10)

        return enemy(health, attack, special, chance, adjective+" "+animal)

    else:
        health = random.randint(200,250)
        attack = random.randint(20,40)
        special = random.randint(50,60)
        chance = random.randint(1,8)
        superMove = random.randint(100,200)

        return boss(health, attack, special, chance, adjective+" "+animal, superMove)

def enemyAttack(hitChance, attackValue, name, defence):
    print(name, "is winding up for an attack...")
    hit = random.randint(0,10)
    if hitChance >= hit:
        print("it hits the hero!!!")
        loss = max(0, attackValue - defence)
        print("You stagger losing...", loss, "health")
        return math.ceil(loss)
    else:
        print("The enemy misses!")
        return 0

def hitChance(luck):
    hit = random.randint(0,4)
    if luck < hit:
        print("MISS!")
        return False

    else:
        print("You hit the enemy!")
        return True

def isDead(health):
    if health < 1:
        return True
    else:
        return False

def loot(luck, genCharacter):
    lootChance = random.randint(0,4)
    if luck < lootChance:
        print("NO LOOT FOR YOU!")

    else:
        tableNum = random.randint(0,4)
        lootTableList = ["items","ranged","defence","magic","attack"]
        itemType = lootTableList[tableNum]
        lines = loadLines(itemType+".txt", [])

        print("The enemy dropped a....")

        if len(lines) == 0:
            print("NO LOOT FOR YOU!")
            return

        item = random.randint(0,len(lines)-1)

        itemLine = lines[item]
        splitItemLine = itemLine.split(",")

        name = splitItemLine[0]
        value = int(splitItemLine[1])

        print(name)

        if itemType == "attack":
            genCharacter.setAttack(genCharacter.getAttack()+value)
            print("Your new attack is...")
            print(genCharacter.getAttack())

        elif itemType == "ranged":
            genCharacter.setRanged(genCharacter.getRanged()+value)
            print("Your new Ranged Attack is...")
            print(genCharacter.getRanged())

        elif itemType == "defence":
            genCharacter.setDefence(genCharacter.getDefence()+value)
            print("Your new attack is...")
            print(genCharacter.getDefence())

        elif itemType == "magic":
            genCharacter.setMagic(genCharacter.getMagic()+value)
            print("Your new Magic attack is...")
            print(genCharacter.getMagic())

        else:
            
            if splitItemLine[2] == "luck":
                genCharacter.setLuck(genCharacter.getLuck()+value)
                print("Your new Luck  is...")
                print(genCharacter.getLuck())

            elif splitItemLine[2] == "health":
                genCharacter.setHealth(genCharacter.getHealth()+value)
                print("Your new Health  is...")
                print(genCharacter.getHealth())

                                     
                                    
genCharacter = hero(100, 10, 11, 12, 1, 14, "LEE!")


pprint(vars(genCharacter))

loot(100,genCharacter)
loot(100,genCharacter)
loot(100,genCharacter)
loot(100,genCharacter)
loot(100,genCharacter)
loot(100,genCharacter)
loot(100,genCharacter)
loot(100,genCharacter)
loot(100,genCharacter)

pprint(vars(genCharacter))

    
