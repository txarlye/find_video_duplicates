#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Paquete de servicios de Plex para gestión de ediciones
"""

from .plex_editions_detector import PlexEditionsDetector
from .plex_edition_creator import PlexEditionCreator
from .plex_duplicate_analyzer import PlexDuplicateAnalyzer
from .plex_editions_manager import PlexEditionsManager

__all__ = [
    'PlexEditionsDetector',
    'PlexEditionCreator', 
    'PlexDuplicateAnalyzer',
    'PlexEditionsManager'
]
