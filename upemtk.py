#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Fichier upemtk.py
# Bibliothèque graphique simplifiée utilisant le module tkinter
# Dérivé de iutk.py, IUT de Champs-sur-Marne, 2013-2014

# Dernière mise à jour : Nov. 2019

import subprocess
import sys
import tkinter as tk
from collections import deque
from time import time, sleep
from tkinter.font import Font
from typing import Union

__all__ = [
    # gestion de fenêtre
    'creer_fenetre',
    'fermer_fenetre',
    'rafraichir',
    # dessin
    'ligne',
    'fleche',
    'polygone',
    'rectangle',
    'cercle',
    'point',
    'image',
    'texte',
    'taille_texte',
    # effacer
    'effacer_tout',
    'effacer',
    # utilitaires
    'attendre',
    'capture_ecran',
    'touche_pressee',
    'premier_plan',
    'arriere_plan',
    # événements
    'donner_ev',
    'attendre_ev',
    'attendre_clic_gauche',
    'attendre_clic_droit',
    'attendre_fermeture',
    'ecouter_ev',
    'supprimer_ecouteur',
    'type_ev',
    'abscisse',
    'ordonnee',
    'touche'
]


class CustomCanvas:
    """
    Classe qui encapsule tous les objets tkinter nécessaires à la création
    d'un canevas.
    """

    _on_osx = sys.platform.startswith("darwin")
    _ev_mapping = {
        'ClicGauche': '<Button-1>',
        'DoubleClicGauche': '<Double-Button-1>',
        'ClicMilieu': '<Button-2>',
        'ClicDroit': '<Button-2>' if _on_osx else '<Button-3>',
        'Deplacement': '<Motion>',
        'Roulette': '<MouseWheel>',
        'Touche': '<Key>'
    }
    _default_ev = ['ClicGauche', 'ClicDroit', 'Touche']

    def __init__(self, width, height, refresh_rate=100, events=None, name=None):
        # width and height of the canvas
        self.width = width
        self.height = height
        self.period = 1 / refresh_rate

        # root Tk object
        self.root = tk.Tk()
        self.root.title(name or 'Tk')

        # canvas attached to the root object
        self.canvas = tk.Canvas(self.root, width=width,
                                height=height, highlightthickness=0)

        # adding the canvas to the root window and giving it focus
        self.canvas.pack()
        self.canvas.focus_set()

        # binding events
        self.ev_queue = deque()
        self.ev_listeners = dict()
        self.buttons = set()
        self.pressed_keys = set()
        self.events = events or CustomCanvas._default_ev
        self.bind_events()

        # marque
        self.tailleMarque = 5

        # update for the first time
        self.last_update = time()
        self.root.update()

    def update(self):
        t = time()
        self.root.update()
        sleep(max(0., self.period - (t - self.last_update)))
        self.last_update = time()

    def bind_events(self):
        self.root.protocol("WM_DELETE_WINDOW", self.event_quit)
        self.canvas.bind('<KeyPress>', self.register_key)
        self.canvas.bind('<KeyRelease>', self.release_key)
        for name in self.events:
            self.bind_event(name)

    def register_key(self, ev):
        self.pressed_keys.add(ev.keysym)

    def release_key(self, ev):
        if ev.keysym in self.pressed_keys:
            self.pressed_keys.remove(ev.keysym)

    def event_quit(self):
        self.ev_queue.append(("Quitte", ""))

    def bind_event(self, name):
        e_type = CustomCanvas._ev_mapping.get(name, name)

        def handler(event, _name=name):
            self.ev_queue.append((_name, event))

        self.canvas.bind(e_type, handler, True)

    def register_listener(self, name, f, args, kwargs):
        e_type = CustomCanvas._ev_mapping.get(name, name)

        def handler(event, _name=name, _f=f):
            _f((_name, event), *args, **kwargs)

        listener_id = self.canvas.bind(e_type, handler, True)
        self.ev_listeners[listener_id] = e_type
        return listener_id

    def unregister_listener(self, listener_id):
        e_type = self.ev_listeners[listener_id]
        self.canvas.unbind(e_type, listener_id)
        del self.ev_listeners[listener_id]

    def unbind_event(self, name):
        e_type = CustomCanvas._ev_mapping.get(name, name)
        self.canvas.unbind(e_type)


__canvas = None
__img = dict()


##############################################################################
# Exceptions
#############################################################################


class EventAttributeError(Exception):
    pass


class WindowError(Exception):
    pass


class EventListenerError(Exception):
    pass


#############################################################################
# Initialisation, mise à jour et fermeture
#############################################################################


def creer_fenetre(largeur, hauteur, frequence=100, nom=None, evenement=None):
    """
    Crée une fenêtre de dimensions ``largeur`` x ``hauteur`` pixels.
    """
    global __canvas
    if __canvas:
        raise WindowError(
            "La fenêtre a déjà été créée avec la fonction \"creer_fenetre\" !"
        )
    __canvas = CustomCanvas(largeur, hauteur, frequence, name=nom, events=evenement)


def fermer_fenetre():
    """
    Détruit la fenêtre.
    """
    global __canvas
    if not __canvas:
        raise WindowError(
            "La fenêtre n'a pas été créée avec la fonction \"creer_fenetre\" !")
    __canvas.root.destroy()
    __canvas = None


def rafraichir():
    """
    Met à jour la fenêtre. Les dessins ne sont affichés qu'après
    l'appel à  cette fonction.
    """
    if not __canvas:
        raise WindowError(
            "La fenêtre n'a pas été créée avec la fonction \"creer_fenetre\" !")
    __canvas.update()


#############################################################################
# Fonctions de dessin
#############################################################################


# Formes géométriques

def ligne(ax: float, ay: float, bx: float, by: float, couleur: str = "black",
          epaisseur: float = 1, tag: str = ""):
    """
    Trace un segment reliant le point ``(ax, ay)`` au point ``(bx, by)``.

    :param ax: Abscisse du premier point.
    :param ay: Ordonnée du premier point.
    :param bx: Abscisse du second point.
    :param by: Ordonnée du second point.
    :param couleur: Couleur de trait (défaut 'black').
    :param epaisseur: Épaisseur de trait en pixels (défaut 1).
    :param tag: Étiquette d'objet (défaut : pas d'étiquette).
    :return: Identificateur d'objet
    """
    return __canvas.canvas.create_line(
        ax, ay, bx, by,
        fill=couleur,
        width=epaisseur,
        tag=tag)


def fleche(ax: float, ay: float, bx: float, by: float, couleur: str = "black",
           epaisseur: float = 1, tag: str = ""):
    """
    Trace une flèche du point ``(ax, ay)`` au point ``(bx, by)``.

    :param ax: Abscisse du premier point.
    :param ay: Ordonnée du premier point.
    :param bx: Abscisse du second point.
    :param by: Ordonnée du second point.
    :param couleur: Couleur de trait (défaut 'black').
    :param epaisseur: Épaisseur de trait en pixels (défaut 1).
    :param tag: Étiquette d'objet (défaut : pas d'étiquette).
    :return: Identificateur d'objet
    """
    x, y = (bx - ax, by - ay)
    n = (x ** 2 + y ** 2) ** .5
    x, y = x / n, y / n
    points = [bx, by,
              bx - x * 5 - 2 * y,
              by - 5 * y + 2 * x,
              bx - x * 5 + 2 * y,
              by - 5 * y - 2 * x]
    return __canvas.canvas.create_polygon(
        points,
        fill=couleur,
        outline=couleur,
        width=epaisseur,
        tag=tag)


def polygone(points: list, couleur: str = "black", remplissage: str = "",
             epaisseur: float = 1, tag: str = ""):
    """
    Trace un polygone dont la liste de points est fournie.

    :param points: Liste de couples (abscisse, ordonnée) de points.
    :param couleur: Couleur de trait (défaut 'black').
    :param remplissage: Couleur de fond (défaut transparent).
    :param epaisseur: Épaisseur de trait en pixels (défaut 1).
    :param tag: Étiquette d'objet (défaut : pas d'étiquette).
    :return: Identificateur d'objet.
    """
    return __canvas.canvas.create_polygon(
        points,
        fill=remplissage,
        outline=couleur,
        width=epaisseur,
        tag=tag)


def rectangle(ax: float, ay: float, bx: float, by: float,
              couleur: str = "black", remplissage: str = "",
              epaisseur: float = 1, tag: str = ""):
    """
    Trace un rectangle noir ayant les point ``(ax, ay)`` et ``(bx, by)``
    comme coins opposés.

    :param ax: Abscisse du premier point.
    :param ay: Ordonnée du premier point.
    :param bx: Abscisse du second point.
    :param by: Ordonnée du second point.
    :param couleur: Couleur de trait (défaut 'black').
    :param remplissage: Couleur de fond (défaut transparent).
    :param epaisseur: Épaisseur de trait en pixels (défaut 1).
    :param tag: Étiquette d'objet (défaut : pas d'étiquette).
    :return: Identificateur d'objet
    """
    return __canvas.canvas.create_rectangle(
        ax, ay, bx, by,
        outline=couleur,
        fill=remplissage,
        width=epaisseur,
        tag=tag)


def cercle(x: float, y: float, r: float, couleur: str = "black",
           remplissage: str = "", epaisseur: float = 1, tag: str = ""):
    """
    Trace un cercle de centre ``(x, y)`` et de rayon ``r`` en noir.

    :param x: Abscisse du centre.
    :param y: Ordonnée du centre.
    :param r: Rayon du cercle.
    :param couleur: Couleur de trait (défaut 'black').
    :param remplissage: Couleur de fond (défaut transparent).
    :param epaisseur: Épaisseur de trait en pixels (défaut 1).
    :param tag: Étiquette d'objet (défaut : pas d'étiquette).
    :return: Identificateur d'objet
    """
    return __canvas.canvas.create_oval(
        x - r, y - r, x + r, y + r,
        outline=couleur,
        fill=remplissage,
        width=epaisseur,
        tag=tag)


def arc(x: float, y: float, r: float, ouverture: float = 90,
        depart: float = 0, couleur: str = 'black', remplissage: str = '',
        epaisseur: float = 1, tag: str = ''):
    """
    Trace un arc de cercle de centre ``(x, y)``, de rayon ``r`` et
    d'angle d'ouverture ``ouverture`` (défaut : 90 degrés, dans le sens
    contraire des aiguilles d'une montre) depuis l'angle initial ``depart``
    (défaut : direction 'est').

    :param x: Abscisse du centre.
    :param y: Ordonnée du centre.
    :param r: Rayon de l'arc.
    :param ouverture: Angle d'ouverture.
    :param depart: Angle de départ.
    :param couleur: Couleur de trait (défaut 'black').
    :param remplissage: Couleur de fond (défaut transparent).
    :param epaisseur: Épaisseur de trait en pixels (défaut 1).
    :param tag: Étiquette d'objet (défaut : pas d'étiquette).
    :return: Identificateur d'objet
    """
    return __canvas.canvas.create_arc(
        x - r, y - r, x + r, y + r,
        extent=ouverture,
        start=depart,
        style=tk.ARC,
        outline=couleur,
        fill=remplissage,
        width=epaisseur,
        tag=tag)


def point(x: float, y: float, couleur: str = 'black',
          epaisseur: float = 1, tag: str = ''):
    """
    Trace un point aux coordonnées ``(x, y)`` en noir.

    :param x: Abscisse du point.
    :param y: Ordonnée du point.
    :param couleur: Couleur de trait (défaut 'black').
    :param epaisseur: Épaisseur de trait en pixels (défaut 1).
    :param tag: Étiquette d'objet (défaut : pas d'étiquette).
    :return: Identificateur d'objet
    """
    return cercle(x, y, epaisseur,
                  couleur=couleur,
                  remplissage=couleur,
                  tag=tag)


# Image

def image(x: float, y: float, fichier: str, ancrage: str = 'center',
          tag: str = ''):
    """
    Affiche l'image contenue dans ``fichier`` avec ``(x, y)`` comme centre.
    Les valeurs possibles du point d'ancrage sont ``'center'``, ``'nw'``, etc.

    :param x: Abscisse du point d'ancrage.
    :param y: Ordonnée du point d'ancrage.
    :param fichier: Nom du fichier contenant l'image.
    :param ancrage: Position du point d'ancrage par rapport à l'image.
    :param tag: Étiquette d'objet (défaut : pas d'étiquette).
    :return: Identificateur d'objet.
    """
    img = tk.PhotoImage(file=fichier)
    img_object = __canvas.canvas.create_image(
        x, y, anchor=ancrage, image=img, tag=tag)
    __img[img_object] = img
    return img_object


# Texte

def texte(x: float, y: float, chaine: str, couleur: str = 'black',
          ancrage: str = 'nw', police: str = 'Helvetica', taille: int = 24,
          tag: str = ''):
    """
    Affiche la chaîne ``chaine`` avec ``(x, y)`` comme point d'ancrage (par
    défaut le coin supérieur gauche).

    :param x: Abscisse du point d'ancrage.
    :param y: Ordonnée du point d'ancrage.
    :param chaine: Texte à afficher.
    :param couleur: Couleur du texte (défaut 'black').
    :param ancrage: Position du point d'ancrage (défaut 'nw').
    :param police: Police de caractères (défaut : `Helvetica`).
    :param taille: Taille de police (défaut 24).
    :param tag: Étiquette d'objet (défaut : pas d'étiquette).
    :return: Identificateur d'objet.
    """
    return __canvas.canvas.create_text(
        x, y,
        text=chaine, font=(police, taille), tag=tag,
        fill=couleur, anchor=ancrage)


def taille_texte(chaine: str, police: str = 'Helvetica', taille: int = 24):
    """
    Donne la largeur et la hauteur en pixel nécessaires pour afficher
    ``chaine`` dans la police et la taille données.

    :param chaine: Chaîne à mesurer.
    :param police: Police de caractères (défaut : `Helvetica`).
    :param taille: Taille de police (défaut 24).
    :return: Couple (w, h) constitué de la largeur et la hauteur de la chaîne
        en pixels (int), dans la police et la taille données.
    """
    font = Font(family=police, size=taille)
    return font.measure(chaine), font.metrics("linespace")


#############################################################################
# Effacer
#############################################################################

def effacer_tout():
    """
    Nettoie la fenêtre.
    """
    __img.clear()
    __canvas.canvas.delete("all")


def effacer(objet: Union[int, str]):
    """
    Efface ``objet`` de la fenêtre.

    :param objet: Objet ou étiquette d'objet à supprimer
    """
    if objet in __img:
        del __img[objet]
    __canvas.canvas.delete(objet)


#############################################################################
# Utilitaires
#############################################################################


def attendre(temps: float):
    """
    Bloque temporairement le programme.
    :param temps: Temps à attendre.
    """
    start = time()
    while time() - start < temps:
        rafraichir()


def capture_ecran(file: str):
    """
    Fait une capture d'écran sauvegardée dans ``file.png``.
    """
    __canvas.canvas.postscript(file=file + ".ps", height=__canvas.height,
                               width=__canvas.width, colormode="color")

    subprocess.call(
        "convert -density 150 -geometry 100% -background white -flatten"
        " " + file + ".ps " + file + ".png", shell=True)
    subprocess.call("rm " + file + ".ps", shell=True)


def touche_pressee(keysym: str):
    """
    Renvoie `True` si ``keysym`` est actuellement pressée.
    :param keysym: Symbole associé à la touche à tester.
    :return: `True` si ``keysym`` est actuellement pressée, `False` sinon.
    """
    return keysym in __canvas.pressed_keys


def premier_plan(tag: Union[int, str]):
    """
    Place l'objet passé en paramètre au premier plan.
    :param tag: Identifiant de l'objet.
    """
    if not __canvas:
        raise WindowError(
            "La fenêtre n'a pas été créée avec la fonction \"creer_fenetre\" !")
    __canvas.canvas.tag_raise(tag)


def arriere_plan(tag: Union[int, str]):
    """
    Place l'objet passé en paramètre à l'arrière plan.
    :param tag: Identifiant de l'objet.
    """
    if not __canvas:
        raise WindowError(
            "La fenêtre n'a pas été créée avec la fonction \"creer_fenetre\" !")
    __canvas.canvas.tag_lower(tag)


#############################################################################
# Gestions des évènements
#############################################################################

def donner_ev():
    """
    Renvoie immédiatement l'événement en attente le plus ancien,
    ou ``None`` si aucun événement n'est en attente.
    """
    if __canvas is None:
        raise WindowError(
            "La fenêtre n'a pas été créée avec la fonction \"cree_fenetre\".")
    if __canvas.ev_queue:
        return __canvas.ev_queue.popleft()
    return None


def attendre_ev():
    """Attend qu'un événement ait lieu et renvoie le premier événement qui
    se produit."""
    while True:
        ev = donner_ev()
        if ev:
            return ev
        rafraichir()


def attendre_clic_gauche():
    """Attend qu'un clic gauche sur la fenêtre ait lieu et renvoie ses
    coordonnées. **Attention**, cette fonction empêche la détection d'autres
    événements ou la fermeture de la fenêtre."""
    while True:
        ev = donner_ev()
        if ev and type_ev(ev) == 'ClicGauche':
            return abscisse(ev), ordonnee(ev)
        rafraichir()


def attendre_clic_droit():
    """Attend qu'un clic droit sur la fenêtre ait lieu et renvoie ses
    coordonnées. **Attention**, cette fonction empêche la détection d'autres
    événements ou la fermeture de la fenêtre."""
    while True:
        ev = donner_ev()
        if ev and type_ev(ev) == 'ClicDroit':
            return abscisse(ev), ordonnee(ev)
        rafraichir()


def attendre_fermeture():
    """Attend la fermeture de la fenêtre. Cette fonction renvoie None."""
    while True:
        ev = donner_ev()
        if ev and type_ev(ev) == 'Quitte':
            fermer_fenetre()
            return
        rafraichir()


def ecouter_ev(nom_ev: str, func: callable, *args, **kwargs):
    """
    Exécute la fonction passée en paramètre lorsque
    l'événement ``nom_ev`` survient.
    :param nom_ev: Nom de l'événement écouté.
    :param func: Fonction exécutée.
    :param args: Liste des arguments à passer à la fonction.
    :return: Identifiant de l'écouteur.
    """
    if not __canvas:
        raise WindowError(
            "La fenêtre n'a pas été créée avec la fonction \"cree_fenetre\".")
    if func.__code__.co_argcount < 1:
        raise EventListenerError(
            f"La fonction {func.__name__} doit avoir au moins un paramètre !")
    return __canvas.register_listener(nom_ev, func, args, kwargs)


def supprimer_ecouteur(listener_id: str):
    """
    Supprimer un écouteur d'événement.
    :param listener_id: Identifiant de l'écouteur.
    """
    if not __canvas:
        raise WindowError(
            "La fenêtre n'a pas été créée avec la fonction \"cree_fenetre\".")
    if listener_id not in __canvas.ev_listeners:
        raise EventListenerError(
            f"L'écouteur d'événement {listener_id} n'existe pas !")
    __canvas.unregister_listener(listener_id)


def type_ev(ev: tuple):
    """
    Renvoie une chaîne donnant le type de ``ev``. Les types
    possibles sont 'ClicDroit', 'ClicGauche', 'Touche' et 'Quitte'.
    Renvoie ``None`` si ``evenement`` vaut ``None``.
    """
    return ev if ev is None else ev[0]


def abscisse(ev: tuple):
    """
    Renvoie la coordonnée x associé à ``ev`` si elle existe, None sinon.
    """
    return attribut(ev, 'x')


def ordonnee(ev: tuple):
    """
    Renvoie la coordonnée y associé à ``ev`` si elle existe, None sinon.
    """
    return attribut(ev, 'y')


def touche(ev: tuple):
    """
    Renvoie une chaîne correspondant à la touche associé à ``ev``,
    si elle existe.
    """
    return attribut(ev, 'keysym')


def attribut(ev: tuple, nom: str):
    if ev is None:
        raise EventAttributeError(
            f"Accès à l'attribut {nom} impossible sur un événement vide")
    t, e = ev
    if hasattr(e, nom):
        return getattr(e, nom)
    else:
        raise EventAttributeError(
            f"Accès à l'attribut {nom} impossible sur un événement de type", t)
