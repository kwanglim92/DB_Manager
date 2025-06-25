# -*- coding: utf-8 -*-
"""
한글 폰트 설정 모듈
"""

import tkinter as tk
import tkinter.font as tkFont

def setup_korean_font():
    """한글 폰트 설정"""
    # 시스템에서 사용 가능한 한글 폰트 찾기
    font_candidates = [
        ('맑은 고딕', 9),
        ('굴림', 9), 
        ('돋움', 9),
        ('나눔고딕', 9),
        ('Arial Unicode MS', 9),
        ('DejaVu Sans', 9),
        ('TkDefaultFont', 9)
    ]
    
    korean_font = None
    for font_name, size in font_candidates:
        try:
            test_font = tkFont.Font(family=font_name, size=size)
            korean_font = test_font
            break
        except:
            continue
    
    if not korean_font:
        korean_font = tkFont.nametofont("TkDefaultFont")
    
    return korean_font

def apply_korean_font_to_widget(widget, font=None):
    """위젯에 한글 폰트 적용"""
    if font is None:
        font = setup_korean_font()
    
    try:
        widget.configure(font=font)
    except:
        pass
    
    return font

def configure_default_font():
    """기본 폰트를 한글 지원 폰트로 설정"""
    try:
        # Tk root가 생성된 후에만 폰트 설정 가능
        root = tk._default_root
        if root is None:
            return
            
        korean_font = setup_korean_font()
        
        # 기본 폰트들을 한글 지원 폰트로 교체
        default_fonts = ['TkDefaultFont', 'TkTextFont', 'TkMenuFont']
        
        for font_name in default_fonts:
            try:
                font = tkFont.nametofont(font_name)
                font.configure(family=korean_font['family'], size=korean_font['size'])
            except:
                continue
                
    except Exception as e:
        print(f"폰트 설정 실패: {e}")