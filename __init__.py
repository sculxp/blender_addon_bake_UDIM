bl_info = {
    "name": "Bake UDIM Tiles",
    "author": "Alfonso Annarumma",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "Properties > Render Properties > Bake",
    "description": "Baking UDIM Tiles with one click",
    "warning": "",
    "wiki_url": "",
    "category": "Render",
}

import bpy
import os
import bmesh


def uv_traslate(obj, u, v):
    me = obj.data
    bm = bmesh.from_edit_mesh(me)

    uv_layer = bm.loops.layers.uv.verify()
    # bm.faces.layers.tex.verify()  # currently blender needs both layers.

    # scale UVs x2
    for f in bm.faces:
        for l in f.loops:
            l[uv_layer].uv[0] -= u
            l[uv_layer].uv[1] -= v

    # bm.to_mesh(me)
    me.update()


def bake_udim(context):
    obj = context.scene.view_layers[0].objects.active

    data = bpy.data
    images = data.images

    mat = obj.active_material
    nodes = mat.node_tree.nodes

    if nodes.active.type == 'TEX_IMAGE':
        if nodes.active.image.source == 'TILED':
            udim_node = nodes.active
            udim = udim_node.image
            basename = bpy.path.basename(udim.filepath)
            udim_name = basename.split('.')[0]
            udim_dir = os.path.dirname(bpy.path.abspath(udim.filepath))
            split = udim.filepath.split('.')
            ext = split[-1]

            udim_list = []
            for t in udim.tiles:
                udim_list.append(t.number)

            added_nodes = []
            bake = images.new("bake", udim.size[0], udim.size[1], alpha=False, float_buffer=udim.is_float,
                              stereo3d=False, is_data=False, tiled=False)
            for one_mat in obj.data.materials:
                one_nodes = one_mat.node_tree.nodes
                bake_node = one_nodes.new("ShaderNodeTexImage")
                bake_node.name = "bake_image"
                one_nodes.active = bake_node
                bake_node.image = bake
                bake_node.select = True
                one_nodes.active = bake_node
                added_nodes.append((one_nodes, bake_node))

            try:
                for n in udim_list:

                    v = (n - 1001) // 10
                    u = n - 1001 - v * 10

                    if obj.mode != 'EDIT':
                        bpy.ops.object.editmode_toggle()

                        uv_traslate(obj, u, v)

                    try:
                        if obj.mode == 'EDIT':
                            bpy.ops.object.editmode_toggle()

                        filepath = udim_dir + '/' + udim_name + '.' + str(n) + "." + ext
                        print(filepath)
                        bake.filepath = filepath

                        bake_type = bpy.context.scene.cycles.bake_type
                        bpy.ops.object.bake(type=bake_type, filepath=filepath, save_mode='EXTERNAL')

                        bake.save()

                    finally:
                        if obj.mode != 'EDIT':
                            bpy.ops.object.editmode_toggle()

                            uv_traslate(obj, -u, -v)

                        if obj.mode == 'EDIT':
                            bpy.ops.object.editmode_toggle()
            finally:
                for bake_node in added_nodes:
                    bake_node[0].remove(bake_node[1])

                if bake is not None:
                    images.remove(bake)

            nodes.active = udim_node
            udim.reload()
        else:
            print("Select Udim Node")
    else:
        print("Select Udim Node")


class SCENE_OT_Bake_Udim(bpy.types.Operator):
    """Select a UDIM Image Node"""
    bl_idname = "object.bake_udim"
    bl_label = "Bake for UDIM Image"

    @classmethod
    def poll(cls, context):
        if context.active_object is None or context.active_object.active_material is None:
            return False
        nodes = context.active_object.active_material.nodes
        return nodes.active.type == 'TEX_IMAGE' and nodes.active.image.source == 'TILED'

    def execute(self, context):
        bake_udim(bpy.context)

        return {'FINISHED'}


def menu_func(self, context):
    layout = self.layout
    layout.operator("object.bake_udim")


def register():
    bpy.utils.register_class(SCENE_OT_Bake_Udim)
    bpy.types.CYCLES_RENDER_PT_bake.append(menu_func)


def unregister():
    bpy.utils.unregister_class(SCENE_OT_Bake_Udim)
    bpy.types.CYCLES_RENDER_PT_bake.remove(menu_func)


if __name__ == "__main__":
    register()
