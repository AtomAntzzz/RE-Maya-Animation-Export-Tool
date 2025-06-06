# RE Maya Animation Export Tool
# Version: v0.12
# Last Release: June 4, 2025
# Author: AtomAntzzz

import maya.cmds as cmds
import maya.mel as mel
import re
import os


class AnimationExporterUI:
    def __init__(self):
        self.window_name = "animationExporterWindow"
        self.animation_data = []
        self.create_ui()
    
    def create_ui(self):
        """创建UI界面"""
        # 如果窗口已存在，删除它
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
        
        # 创建窗口
        self.window = cmds.window(
            self.window_name,
            title="RE Maya Animation Export Tool",
            widthHeight=(420, 500),  # 增加窗口高度以容纳新按钮
            resizeToFitChildren=True,
            sizeable=False
        )
        
        # 主布局
        main_layout = cmds.columnLayout(
            adjustableColumn=True,
            columnAttach=('both', 15),
            rowSpacing=12,
            parent=self.window
        )
        
        # 标题
        cmds.text(label="RE Maya Animation Export Tool", font="boldLabelFont", height=25)
        cmds.separator(height=15, style="in")
        
        # Paste Noesis List按钮
        self.paste_button = cmds.button(
            label="Paste Noesis List",
            command=self.show_input_dialog,
            height=35,
            backgroundColor=(0.45, 0.55, 0.7)
        )
        
        # 添加fixframerateforDD2按钮
        self.fix_framerate_button = cmds.button(
            label="Fix Frame Rate for DD2",
            command=self.fix_framerate_for_dd2,
            height=35,
            backgroundColor=(0.7, 0.45, 0.6),
            annotation="Convert animation from 30fps to 60fps with frame offset for DD2 compatibility"
        )
        
        cmds.separator(height=15)
        
        # 动画列表标签和下拉框
        cmds.text(label="Animation List:", align="left", font="boldLabelFont")
        self.animation_combo = cmds.optionMenu(
            label="",
            enable=False,
            changeCommand=self.on_animation_selected,
            height=25
        )
        cmds.menuItem(label="No animations loaded", parent=self.animation_combo)
        
        # 添加 Set Timeline Range 按钮
        self.set_timeline_button = cmds.button(
            label="Set Timeline to Selected Animation",
            command=self.set_timeline_range,
            height=30,
            enable=False,
            backgroundColor=(0.6, 0.5, 0.8),
            annotation="Adjust Maya timeline to match the selected animation's frame range"
        )
        
        cmds.separator(height=15)
        
        cmds.text(label="Export Options:", align="left", font="boldLabelFont")
        
        # 单选按钮组
        self.radio_collection = cmds.radioCollection()
        
        self.export_selected_radio = cmds.radioButton(
            label="Export Selected Animation",
            collection=self.radio_collection,
            select=True,
            onCommand=self.on_export_option_changed
        )
        
        self.export_all_radio = cmds.radioButton(
            label="Export All Animations",
            collection=self.radio_collection,
            onCommand=self.on_export_option_changed
        )
        
        # 导出按钮
        self.export_button = cmds.button(
            label="Export",
            command=self.export_animation,
            height=40,
            enable=False,
            backgroundColor=(0.4, 0.7, 0.4)
        )
        
        cmds.separator(height=15)
        
        # 状态标签
        self.status_text = cmds.text(
            label="Ready - Please paste Noesis animation list first",
            align="center",
            backgroundColor=(0.25, 0.25, 0.25),
            height=25
        )
        
        # 显示窗口
        cmds.showWindow(self.window)
    
    def fix_framerate_for_dd2(self, *args):
        """修复DD2动画帧速率为60fps"""
        try:
            # 检查是否有选中的对象
            selected_objects = cmds.ls(selection=True, long=True)
            if not selected_objects:
                cmds.warning("Please select an object first!")
                self.update_status("Error: No object selected for DD2 frame rate fix")
                return
            
            self.update_status("Applying DD2 frame rate fix...")
            
            # 步骤1: 设置帧速率为30fps
            cmds.currentUnit(time='ntsc')  # 30fps
            print("Step 1: Set frame rate to 30fps")
            
            # 步骤2: 选择当前选中物体的所有子级
            mel.eval('select -hierarchy;')
            print(f"Step 2: Selected All Hierarchy")
            
            # 步骤3: 将时间缩短一半
            try:
                # 对选中的所有对象执行时间缩放
                mel.eval('scaleKey -timeScale 0.5 -timePivot 0;')
                print("Step 3: Applied time scale 0.5 with pivot at frame 0")
                
            except Exception as e:
                print(f"Warning during scaleKey operation: {str(e)}")
                # 即使scaleKey失败也继续执行后续步骤
            
            # 步骤4: 设置帧速率为60fps
            cmds.currentUnit(time='ntscf')  # 60fps
            print("Step 4: Set frame rate to 60fps")
            
            # 完成
            self.update_status("DD2 frame rate fix completed successfully")
            
            # 显示完成对话框
            cmds.confirmDialog(
                title="DD2 Frame Rate Fix Complete",
                message="Successfully applied DD2 frame rate fix:\n"
                       "Fix animation speed issues caused by incorrect frame rate export settings in Noesis",
                button=["OK"]
            )
            
            print("DD2 frame rate fix completed successfully!")
            
        except Exception as e:
            error_msg = f"DD2 frame rate fix failed: {str(e)}"
            cmds.error(error_msg)
            self.update_status("DD2 frame rate fix failed - Check script editor")
            
            cmds.confirmDialog(
                title="DD2 Frame Rate Fix Error",
                message=f"Failed to apply DD2 frame rate fix:\n{str(e)}",
                button=["OK"],
                icon="critical"
            )
    
    def show_input_dialog(self, *args):
        """显示手动输入对话框"""
        result = cmds.promptDialog(
            title='Paste Noesis Animation List',
            message='Please paste your Noesis animation list here:\n(Example: @ 0 \'animation_name (165 frames) ID: 0\')',
            button=['OK', 'Cancel'],
            defaultButton='OK',
            cancelButton='Cancel',
            dismissString='Cancel',
            scrollableField=True,
            text=""
        )
        
        if result == 'OK':
            text = cmds.promptDialog(query=True, text=True)
            if text.strip():
                self.parse_animation_text(text)
            else:
                self.update_status("No text provided")
                cmds.warning("No animation data provided!")
    
    def parse_animation_text(self, text):
        """解析动画文本数据"""
        try:
            self.animation_data = []
            lines = text.strip().split('\n')
            
            # 匹配Noesis插件fmt_RE_MESH.py中输出的格式
            pattern = r'@\s*(\d+)\s*[\'"]([^\'\"]*)\s*\((\d+)\s*frames\).*ID:\s*(\d+)'
            
            for line in lines:
                line = line.strip()
                if not line or not line.startswith('@'):
                    continue
                
                match = re.search(pattern, line)
                if match:
                    start_frame = int(match.group(1))
                    name = match.group(2).strip()
                    frame_count = int(match.group(3))
                    anim_id = int(match.group(4))
                    
                    self.animation_data.append({
                        'name': name,
                        'start_frame': start_frame,
                        'frame_count': frame_count,
                        'end_frame': start_frame + frame_count - 1,
                        'id': anim_id
                    })
                else:
                    print(f"Warning: Could not parse line: {line}")
            
            # 修正blend pose条目的帧数并重新计算起始帧
            if self.animation_data:
                self.fix_blend_pose_frames()
            
            if self.animation_data:
                # 清空并更新下拉列表
                menu_items = cmds.optionMenu(self.animation_combo, query=True, itemListLong=True)
                if menu_items:
                    cmds.deleteUI(menu_items)
                
                # 添加新的菜单项
                for anim in self.animation_data:
                    display_text = f"{anim['name']} (Frames: {anim['start_frame']}-{anim['end_frame']}, ID: {anim['id']})"
                    cmds.menuItem(label=display_text, parent=self.animation_combo)
                
                # 启用控件
                cmds.optionMenu(self.animation_combo, edit=True, enable=True)
                cmds.button(self.export_button, edit=True, enable=True)
                cmds.button(self.set_timeline_button, edit=True, enable=True)
                
                self.update_status(f"Successfully parsed {len(self.animation_data)} animations")
                print(f"Parsed {len(self.animation_data)} animations successfully")
            else:
                cmds.warning("No valid animation data found in text!")
                self.update_status("No valid animation data found!")
        
        except Exception as e:
            error_msg = f"Failed to parse animation text: {str(e)}"
            cmds.error(error_msg)
            self.update_status("Parse failed - Check script editor for details")
    
    def on_animation_selected(self, *args):
        """动画选择改变时的回调"""
        selected_index = cmds.optionMenu(self.animation_combo, query=True, select=True) - 1
        if 0 <= selected_index < len(self.animation_data):
            anim = self.animation_data[selected_index]
            self.update_status(f"Selected: {anim['name']} ({anim['frame_count']} frames, ID: {anim['id']})")
    
    def set_timeline_range(self, *args):
        """设置timeline范围为选中动画的范围"""
        if not self.animation_data:
            cmds.warning("No animation data available!")
            return
        
        selected_index = cmds.optionMenu(self.animation_combo, query=True, select=True) - 1
        if 0 <= selected_index < len(self.animation_data):
            anim = self.animation_data[selected_index]
            
            try:
                # 设置动画范围
                cmds.playbackOptions(
                    minTime=anim['start_frame'],
                    maxTime=anim['end_frame'],
                    animationStartTime=anim['start_frame'],
                    animationEndTime=anim['end_frame']
                )
                
                # 将当前时间设置为动画开始帧
                cmds.currentTime(anim['start_frame'])
                
                # 更新状态
                self.update_status(f"Timeline set to {anim['name']}: frames {anim['start_frame']}-{anim['end_frame']}")
                
                print(f"Timeline range set to: {anim['start_frame']}-{anim['end_frame']} for animation '{anim['name']}'")
                
            except Exception as e:
                error_msg = f"Failed to set timeline range: {str(e)}"
                cmds.error(error_msg)
                self.update_status("Failed to set timeline range")
        else:
            cmds.warning("Invalid animation selection!")
    
    def fix_blend_pose_frames(self):
        """修正blend pose条目的帧数并重新计算起始帧"""
        corrected_animations = []
        current_start_frame = 0
        
        for i, anim in enumerate(self.animation_data):
            # 检查是否是blend pose条目（包含_blend*_*pose_模式）
            is_blend_pose = "_blend" in anim['name'].lower() and "_pose_" in anim['name'].lower()
            
            if is_blend_pose:
                # 修正blend pose的帧数为1
                corrected_frame_count = 1
                print(f"Corrected blend pose '{anim['name']}': {anim['frame_count']} frames -> {corrected_frame_count} frame")
            else:
                corrected_frame_count = anim['frame_count']
            
            # 重新计算起始帧
            if i == 0:
                # 第一个动画保持原始起始帧
                new_start_frame = anim['start_frame']
            else:
                # 后续动画的起始帧基于前一个动画的结束帧+1
                new_start_frame = current_start_frame
            
            new_end_frame = new_start_frame + corrected_frame_count - 1
            
            corrected_anim = {
                'name': anim['name'],
                'start_frame': new_start_frame,
                'frame_count': corrected_frame_count,
                'end_frame': new_end_frame,
                'id': anim['id'],
                'original_frame_count': anim['frame_count']  # 保存原始帧数用于调试
            }
            
            corrected_animations.append(corrected_anim)
            
            # 更新下一个动画的起始帧
            current_start_frame = new_end_frame + 1
            
            # 如果有修正，输出调试信息
            if is_blend_pose or new_start_frame != anim['start_frame']:
                print(f"Animation '{anim['name']}': "
                      f"start {anim['start_frame']}->{new_start_frame}, "
                      f"frames {anim['frame_count']}->{corrected_frame_count}, "
                      f"end {anim['end_frame']}->{new_end_frame}")
        
        # 替换原始数据
        self.animation_data = corrected_animations
        
        # 统计修正的数量
        blend_pose_count = sum(1 for anim in corrected_animations 
                              if "_blend" in anim['name'].lower() and "_pose_" in anim['name'].lower())
        if blend_pose_count > 0:
            print(f"Fixed {blend_pose_count} blend pose animations and recalculated frame ranges")
    
    def on_export_option_changed(self, *args):
        """导出选项改变时的处理"""
        selected_radio = cmds.radioCollection(self.radio_collection, query=True, select=True)
        
        # 使用字符串比较来判断选中的单选按钮
        if cmds.radioButton(self.export_selected_radio, query=True, select=True):
            # Export Selected Animation 被选中
            if self.animation_data:  # 只有在有动画数据时才启用下拉列表
                cmds.optionMenu(self.animation_combo, edit=True, enable=True)
                cmds.button(self.set_timeline_button, edit=True, enable=True)
                selected_index = cmds.optionMenu(self.animation_combo, query=True, select=True) - 1
                if 0 <= selected_index < len(self.animation_data):
                    anim = self.animation_data[selected_index]
                    self.update_status(f"Export mode: Selected animation - {anim['name']}")
                else:
                    self.update_status("Export mode: Selected animation")
            else:
                cmds.optionMenu(self.animation_combo, edit=True, enable=False)
                cmds.button(self.set_timeline_button, edit=True, enable=False)
                self.update_status("Export mode: Selected animation (No animations loaded)")
        else:
            # Export All Animations 被选中
            cmds.optionMenu(self.animation_combo, edit=True, enable=False)
            cmds.button(self.set_timeline_button, edit=True, enable=False)
            if self.animation_data:
                self.update_status(f"Export mode: All animations ({len(self.animation_data)} total)")
            else:
                self.update_status("Export mode: All animations (No animations loaded)")
    
    def export_animation(self, *args):
        """导出动画"""
        if not self.animation_data:
            cmds.warning("No animation data to export!")
            return
        
        # 分别导出每个动画
        self.export_animations_separately()
    
    def export_animations_separately(self):
        """分别导出每个动画"""
        # 选择导出文件夹
        export_path = cmds.fileDialog2(
            caption="Select Export Directory",
            fileMode=3,  # 文件夹选择模式
            okCaption="Select"
        )
        
        if not export_path:
            self.update_status("Export cancelled by user")
            return
        
        export_path = export_path[0]
        
        try:
            export_selected = cmds.radioButton(self.export_selected_radio, query=True, select=True)
            
            if export_selected:
                # 导出选中的动画
                selected_index = cmds.optionMenu(self.animation_combo, query=True, select=True) - 1
                if 0 <= selected_index < len(self.animation_data):
                    anim = self.animation_data[selected_index]
                    self.update_status(f"Exporting: {anim['name']}...")
                    self.export_single_animation_as_take(anim, export_path)
                    self.update_status(f"Exported: {anim['name']}")
                    cmds.confirmDialog(
                        title="Export Complete",
                        message=f"Successfully exported: {anim['name']}\nTo: {export_path}",
                        button=["OK"]
                    )
                else:
                    cmds.warning("Invalid animation selection!")
            else:
                # 导出所有动画
                exported_count = 0
                failed_exports = []
                
                for i, anim in enumerate(self.animation_data):
                    try:
                        self.update_status(f"Exporting... {i+1}/{len(self.animation_data)}: {anim['name']}")
                        self.export_single_animation_as_take(anim, export_path)
                        exported_count += 1
                    except Exception as e:
                        failed_exports.append(f"{anim['name']}: {str(e)}")
                        print(f"Failed to export {anim['name']}: {str(e)}")
                
                if failed_exports:
                    self.update_status(f"Export complete: {exported_count}/{len(self.animation_data)} successful")
                    error_message = f"Exported {exported_count}/{len(self.animation_data)} animations.\n\nFailed exports:\n" + "\n".join(failed_exports[:5])
                    if len(failed_exports) > 5:
                        error_message += f"\n... and {len(failed_exports)-5} more"
                    cmds.confirmDialog(
                        title="Export Complete with Errors",
                        message=error_message,
                        button=["OK"],
                        icon="warning"
                    )
                else:
                    self.update_status(f"Export complete: {exported_count} animations")
                    cmds.confirmDialog(
                        title="Export Complete",
                        message=f"Successfully exported all {exported_count} animations to:\n{export_path}",
                        button=["OK"]
                    )
        
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            cmds.error(error_msg)
            self.update_status("Export failed - Check script editor for details")
            cmds.confirmDialog(
                title="Export Error",
                message=f"Export failed:\n{str(e)}",
                button=["OK"],
                icon="critical"
            )
    
    def export_single_animation_as_take(self, anim_data, export_path):
        """导出单个动画片段作为独立的Take"""
        try:
            # 设置FBX导出参数
            self.setup_fbx_export_settings_for_clips()
            
            # 清除现有的动画分割设置
            mel.eval('FBXExportSplitAnimationIntoTakes -clear')
            
            # 创建单个Take
            take_name = f"{anim_data['name']}_ID{anim_data['id']}"
            start_frame = anim_data['start_frame']
            end_frame = anim_data['end_frame']
            
            # 设置烘焙时间范围
            mel.eval(f'FBXExportBakeComplexStart -v {start_frame}')
            mel.eval(f'FBXExportBakeComplexEnd -v {end_frame}')
            
            # 添加Take scripts/others/gameFbxExporter.mel
            mel.eval(f'FBXExportSplitAnimationIntoTakes -v "{take_name}" {start_frame} {end_frame}')
            
            # 检查选择
            selected_objects = cmds.ls(selection=True, long=True)
            if not selected_objects:
                result = cmds.confirmDialog(
                    title="No Selection",
                    message="No objects selected. Export all visible objects?",
                    button=["Yes", "No"],
                    defaultButton="Yes",
                    cancelButton="No",
                    dismissString="No"
                )
                
                if result == "Yes":
                    all_transforms = cmds.ls(type='transform', long=True)
                    visible_objects = [obj for obj in all_transforms 
                                     if cmds.getAttr(f"{obj}.visibility") 
                                     and not cmds.getAttr(f"{obj}.intermediateObject", default=False)]
                    if visible_objects:
                        cmds.select(visible_objects)
                    else:
                        raise Exception("No visible objects found to export!")
                else:
                    raise Exception("Export cancelled - no objects to export!")
            
            # 生成文件名
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', anim_data['name'])
            filename = f"{safe_name}_ID{anim_data['id']}.fbx"
            filepath = os.path.join(export_path, filename).replace('\\', '/')
            
            # 执行导出
            mel.eval(f'FBXExport -f "{filepath}" -s')
            
            # 清理
            mel.eval('FBXExportSplitAnimationIntoTakes -clear')
            
            print(f"Exported animation: {anim_data['name']} (Frames: {start_frame}-{end_frame}, ID: {anim_data['id']}) to {filepath}")
            
        except Exception as e:
            # 确保清理
            mel.eval('FBXExportSplitAnimationIntoTakes -clear')
            raise e
    
    def setup_fbx_export_settings_for_clips(self):
        """设置FBX导出选项用于动画片段"""
        try:
            # 重置FBX导出设置
            mel.eval('FBXResetExport')
            
            # 设置动画导出选项
            mel.eval('FBXExportBakeComplexAnimation -v true')
            mel.eval('FBXExportBakeComplexStep -v 1')
            
            # 导出设置
            mel.eval('FBXExportAnimationOnly -v false')  # 导出几何体和动画
            mel.eval('FBXExportBakeComplexAnimation -v true')
            
            # 启用删除原始Take（这样只保留我们分割的Takes）
            mel.eval('FBXExportDeleteOriginalTakeOnSplitAnimation -v true')
            
            # 其他常用设置
            mel.eval('FBXExportSmoothingGroups -v true')
            mel.eval('FBXExportHardEdges -v false')
            mel.eval('FBXExportTangents -v false')
            mel.eval('FBXExportSmoothMesh -v true')
            mel.eval('FBXExportInstances -v false')
            mel.eval('FBXExportReferencedAssetsContent -v true')
            
            # 单位设置
            mel.eval('FBXExportConvertUnitString "cm"')
            
        except Exception as e:
            print(f"Warning: Some FBX export settings may not be available: {str(e)}")
    
    def update_status(self, message):
        """更新状态显示"""
        cmds.text(self.status_text, edit=True, label=message)
        cmds.refresh()  # 强制刷新界面
    
    def close_window(self):
        """关闭窗口"""
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)


def show_animation_exporter():
    """显示动画导出工具"""
    exporter = AnimationExporterUI()
    return exporter


# 运行脚本
if __name__ == "__main__":
    show_animation_exporter()
