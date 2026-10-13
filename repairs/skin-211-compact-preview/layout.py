"""Scoped, deterministic compact preview XML and vector-derived PNG assets.

No existing theme, font or texture is edited. Every profile gets this one window
definition; the installed native window's actual coordinates own placement.
"""
from pathlib import Path

PREFIX = 'skin.infinity.diggz/'
ASSET_DIR = 'media/infinity_preview/'


def preview_xml():
    return '''<?xml version="1.0" encoding="utf-8"?>
<window>
  <defaultcontrol always="true">81</defaultcontrol>
  <controls>
    <control type="image" id="2">
      <left>0</left><top>0</top><width>100%</width><height>100%</height>
      <texture colordiffuse="40000000">infinity_ui/contract_white.png</texture>
    </control>
    <control type="group" id="1">
      <left>0</left><top>0</top><width>680</width><height>440</height>
      <visible>String.IsEqual(Window.Property(Preview.LayoutReady),true)</visible>
      <control type="image">
        <left>0</left><top>0</top><width>680</width><height>440</height>
        <texture border="24" colordiffuse="$VAR[InfinityLegacySurface]">infinity_preview/compact_surface.png</texture>
      </control>
      <control type="image">
        <left>0</left><top>0</top><width>680</width><height>440</height>
        <texture border="24" colordiffuse="FF24A8FF">infinity_preview/compact_rim.png</texture>
      </control>
      <control type="image">
        <left>32</left><top>32</top><width>128</width><height>128</height>
        <texture border="16" colordiffuse="$VAR[InfinityLegacyField]">infinity_preview/compact_button.png</texture>
      </control>
      <control type="image" id="10">
        <left>52</left><top>38</top><width>88</width><height>116</height>
        <aspectratio>keep</aspectratio><texture>infinity_preview/compact_zip.png</texture>
      </control>
      <control type="label" id="11">
        <left>184</left><top>32</top><width>384</width><height>44</height>
        <label>$INFO[Window.Property(Preview.Title)]</label><font>InfinityBodyBold</font>
        <textcolor>$VAR[InfinityLegacyText]</textcolor><aligny>center</aligny><scroll>true</scroll>
      </control>
      <control type="label" id="12">
        <left>184</left><top>78</top><width>384</width><height>36</height>
        <label>$INFO[Window.Property(Preview.Subtitle)]</label><font>InfinitySmall</font>
        <textcolor>$VAR[InfinityLegacySecondary]</textcolor><aligny>center</aligny><scroll>true</scroll>
      </control>
      <control type="label" id="13">
        <left>184</left><top>126</top><width>432</width><height>36</height>
        <label>$INFO[Window.Property(Preview.Summary)]</label><font>InfinitySmall</font>
        <textcolor>$VAR[InfinityLegacyText]</textcolor><aligny>center</aligny><scroll>true</scroll>
      </control>
      <control type="image">
        <left>600</left><top>24</top><width>56</width><height>56</height>
        <texture colordiffuse="$VAR[InfinityLegacyField]">infinity_preview/compact_circle.png</texture>
      </control>
      <control type="image">
        <left>600</left><top>24</top><width>56</width><height>56</height>
        <texture colordiffuse="FF24A8FF">infinity_preview/compact_circle_rim.png</texture>
        <visible>Control.HasFocus(82)</visible>
      </control>
      <control type="button" id="82">
        <left>588</left><top>12</top><width>80</width><height>80</height><label />
        <texturefocus colordiffuse="$VAR[InfinityLegacyText]">infinity_preview/compact_close.png</texturefocus>
        <texturenofocus colordiffuse="$VAR[InfinityLegacyText]">infinity_preview/compact_close.png</texturenofocus>
        <onleft>81</onleft><onright>80</onright><onup>81</onup><ondown>81</ondown>
      </control>
      <control type="textbox" id="20">
        <left>32</left><top>184</top><width>584</width><height>104</height>
        <font>InfinitySmall</font><textcolor>$VAR[InfinityLegacySecondary]</textcolor>
        <text>$INFO[Window.Property(Preview.Status)]</text><pagecontrol>70</pagecontrol>
        <visible>!String.IsEmpty(Window.Property(Preview.Status))</visible>
      </control>
      <control type="scrollbar" id="70">
        <left>628</left><top>184</top><width>12</width><height>104</height>
        <orientation>vertical</orientation><showonepage>false</showonepage>
        <texturesliderbackground colordiffuse="$VAR[InfinityLegacyField]">infinity_ui/contract_white.png</texturesliderbackground>
        <texturesliderbar colordiffuse="FF24A8FF">infinity_ui/contract_white.png</texturesliderbar>
        <texturesliderbarfocus colordiffuse="FF80CBFF">infinity_ui/contract_white.png</texturesliderbarfocus>
        <textureslidernib colordiffuse="FF24A8FF">infinity_ui/contract_white.png</textureslidernib>
        <textureslidernibfocus colordiffuse="FF80CBFF">infinity_ui/contract_white.png</textureslidernibfocus>
        <visible>!String.IsEmpty(Window.Property(Preview.Status))</visible>
        <onleft>81</onleft><onright>80</onright><onup>82</onup><ondown>81</ondown>
      </control>
      <control type="button" id="81">
        <left>32</left><top>320</top><width>296</width><height>88</height>
        <label>Cancel</label><font>InfinityBodyBold</font><align>center</align><aligny>center</aligny>
        <texturefocus border="16" colordiffuse="$VAR[InfinityLegacyField]">infinity_preview/compact_button.png</texturefocus>
        <texturenofocus border="16" colordiffuse="$VAR[InfinityLegacyField]">infinity_preview/compact_button.png</texturenofocus>
        <textcolor>$VAR[InfinityLegacyText]</textcolor><focusedcolor>$VAR[InfinityLegacyText]</focusedcolor>
        <disabledcolor>$VAR[InfinityLegacyDisabled]</disabledcolor>
        <onleft>82</onleft><onright condition="Control.IsEnabled(80)">80</onright>
        <onright condition="!Control.IsEnabled(80)">82</onright>
        <onup condition="Control.IsVisible(70)">70</onup>
        <onup condition="!Control.IsVisible(70)">82</onup><ondown>82</ondown>
      </control>
      <control type="image">
        <left>32</left><top>320</top><width>296</width><height>88</height>
        <texture border="16" colordiffuse="$VAR[InfinityLegacyBorder]">infinity_preview/compact_button_rim.png</texture>
        <visible>!Control.HasFocus(81)</visible>
      </control>
      <control type="image">
        <left>32</left><top>320</top><width>296</width><height>88</height>
        <texture border="16" colordiffuse="FF80CBFF">infinity_preview/compact_button_rim.png</texture>
        <visible>Control.HasFocus(81)</visible>
      </control>
      <control type="button" id="80">
        <left>352</left><top>320</top><width>296</width><height>88</height>
        <label>Install</label><font>InfinityBodyBold</font><align>center</align><aligny>center</aligny>
        <texturefocus border="16" colordiffuse="FF20A8FF">infinity_preview/compact_button.png</texturefocus>
        <texturenofocus border="16" colordiffuse="FF008CFF">infinity_preview/compact_button.png</texturenofocus>
        <textcolor>FFFFFFFF</textcolor><focusedcolor>FFFFFFFF</focusedcolor><disabledcolor>80FFFFFF</disabledcolor>
        <onleft>81</onleft><onright>82</onright>
        <onup condition="Control.IsVisible(70)">70</onup>
        <onup condition="!Control.IsVisible(70)">82</onup><ondown>82</ondown>
      </control>
      <control type="image">
        <left>352</left><top>320</top><width>296</width><height>88</height>
        <texture border="16" colordiffuse="FF7BCCFF">infinity_preview/compact_button_rim.png</texture>
      </control>
    </control>
  </controls>
</window>
'''.encode('utf-8')


def asset_sources():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>'
    sources = {}
    def add(name, w, h, body):
        sources[name] = svg.format(w=w, h=h, body=body)
    add('compact_surface.png', 96, 96, '<rect x="1.5" y="1.5" width="93" height="93" rx="22.5" fill="white"/>')
    add('compact_rim.png', 96, 96, '<rect x="1.5" y="1.5" width="93" height="93" rx="22.5" fill="none" stroke="white" stroke-width="3"/>')
    add('compact_button.png', 64, 64, '<rect x="1" y="1" width="62" height="62" rx="15" fill="white"/>')
    add('compact_button_rim.png', 64, 64, '<rect x="1.5" y="1.5" width="61" height="61" rx="14.5" fill="none" stroke="white" stroke-width="3"/>')
    add('compact_circle.png', 64, 64, '<circle cx="32" cy="32" r="31" fill="white"/>')
    add('compact_circle_rim.png', 64, 64, '<circle cx="32" cy="32" r="30.5" fill="none" stroke="white" stroke-width="3"/>')
    add('compact_close.png', 80, 80, '<path d="M29 29L51 51M51 29L29 51" stroke="white" stroke-width="4" stroke-linecap="round"/>')
    add('compact_zip.png', 88, 116, '''<defs><linearGradient id="page" x2="1" y2="1"><stop stop-color="#176aae"/><stop offset="1" stop-color="#073d70"/></linearGradient><linearGradient id="fold" x2="1" y2="1"><stop stop-color="#7bd7ff"/><stop offset="1" stop-color="#0783d0"/></linearGradient></defs>
<path d="M13 3H57L84 31V105Q84 113 76 113H13Q5 113 5 105V11Q5 3 13 3Z" fill="url(#page)" stroke="#28b0ff" stroke-width="3"/>
<path d="M57 3V27Q57 31 62 31H84Z" fill="url(#fold)" stroke="#28b0ff" stroke-width="2"/>
<path d="M39 12H47V19H39ZM33 19H41V26H33ZM39 26H47V33H39ZM33 33H41V40H33ZM39 40H47V47H39ZM33 47H41V54H33ZM39 54H47V61H39Z" fill="#ecfaff"/>
<path d="M35 62H45L48 77H32Z" fill="none" stroke="#ecfaff" stroke-width="4" stroke-linejoin="round"/>
<path d="M34 83H19V88H27L18 101V106H35V101H25L34 88ZM40 83H45V106H40ZM51 83H62Q70 83 70 91Q70 99 62 99H56V106H51ZM56 88V94H61Q65 94 65 91Q65 88 61 88Z" fill="white"/>''')
    return sources


def build_assets():
    """Compile fixed SVG paths to PNG during packaging; never at Kodi runtime."""
    return {ASSET_DIR + name: _render_svg(svg)
            for name, svg in asset_sources().items()}


def _render_svg(svg):
    """Render with system librsvg/Cairo; no fonts, network or external images."""
    import ctypes as c
    import ctypes.util
    import xml.etree.ElementTree as ET
    node = ET.fromstring(svg)
    width, height = int(node.attrib['width']), int(node.attrib['height'])
    cairo_name = c.util.find_library('cairo')
    cairo = c.CDLL(cairo_name) if cairo_name else None
    rsvg_name = c.util.find_library('rsvg-2')
    object_name = c.util.find_library('gobject-2.0')
    if cairo is None or not rsvg_name or not object_name:
        raise RuntimeError('Asset generation requires system Cairo and librsvg')
    rsvg, gobject = c.CDLL(rsvg_name), c.CDLL(object_name)
    cairo.cairo_image_surface_create.argtypes = [c.c_int, c.c_int, c.c_int]
    cairo.cairo_image_surface_create.restype = c.c_void_p
    cairo.cairo_create.argtypes = [c.c_void_p]
    cairo.cairo_create.restype = c.c_void_p
    cairo.cairo_destroy.argtypes = [c.c_void_p]
    cairo.cairo_surface_destroy.argtypes = [c.c_void_p]
    rsvg.rsvg_handle_new_from_data.argtypes = [c.c_char_p, c.c_size_t, c.c_void_p]
    rsvg.rsvg_handle_new_from_data.restype = c.c_void_p
    rsvg.rsvg_handle_render_cairo.argtypes = [c.c_void_p, c.c_void_p]
    rsvg.rsvg_handle_render_cairo.restype = c.c_int
    gobject.g_object_unref.argtypes = [c.c_void_p]
    writer_type = c.CFUNCTYPE(c.c_int, c.c_void_p, c.POINTER(c.c_ubyte), c.c_uint)
    cairo.cairo_surface_write_to_png_stream.argtypes = [c.c_void_p, writer_type, c.c_void_p]
    cairo.cairo_surface_write_to_png_stream.restype = c.c_int
    data = svg.encode('utf-8')
    handle = rsvg.rsvg_handle_new_from_data(data, len(data), None)
    if not handle:
        raise RuntimeError('Invalid preview asset SVG')
    surface = cairo.cairo_image_surface_create(0, width, height)
    context = cairo.cairo_create(surface)
    chunks = []
    @writer_type
    def write(_closure, buffer, length):
        chunks.append(c.string_at(buffer, length))
        return 0
    try:
        if not rsvg.rsvg_handle_render_cairo(handle, context):
            raise RuntimeError('Could not render preview asset SVG')
        if cairo.cairo_surface_write_to_png_stream(surface, write, None):
            raise RuntimeError('Could not encode preview asset PNG')
        return b''.join(chunks)
    finally:
        cairo.cairo_destroy(context)
        cairo.cairo_surface_destroy(surface)
        gobject.g_object_unref(handle)


def write_assets(directory):
    directory = Path(directory)
    for relative, data in build_assets().items():
        path = directory / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
