# -*- coding: utf-8 -*-
from PIL import Image, ImageFont, ImageDraw
from decimal import Decimal
from shutil import rmtree
import yaml
import os
import wx

class ConfigSet:
    def __init__(self, Type):
        ConfigDict = configFile.get(Type)
        self.filesPath = ConfigDict.get('importFilesPath')
        self.wildCard = ConfigDict.get('wildCard')
        self.tag = Type
        if Type == 'painting':
            self.paintingPath = ConfigDict.get('importPaintingPath')
        elif Type == 'paintingface':
            self.facePath = ConfigDict.get('importFacePath')
    def Update(self, p1 = None, p2 = None, pf1 = None, pf2 = None):
        if self.tag == 'painting':
            self.filesPath = self.filesPath if p1 == None else p1
            self.paintingPath = self.paintingPath if p2 == None else p2
        elif self.tag == 'paintingface':
            self.filesPath = self.filesPath if pf1 == None else pf1
            self.facePath = self.facePath if pf2 == None else pf2
        return 0
    def UpdateFile(self):
        if self.tag == 'painting':
            updateDict = {
                'painting': {
                    'importFilesPath': self.filesPath,
                    'importPaintingPath': self.paintingPath,
                    'wildCard': self.wildCard
                }
            }
        elif self.tag == 'paintingface':
            updateDict = {
                'paintingface': {
                    'importFilesPath': self.filesPath,
                    'importFacePath': self.facePath,
                    'wildCard': self.wildCard
                }
            }
        configFile.update(updateDict)
        with open('ALPAConfigs.yml', 'w', encoding = 'utf-8') as yamlFile:
            yaml.safe_dump(configFile, yamlFile, allow_unicode = True, sort_keys = False)
        return 0
class RectTransform:
    def __init__(self, filePath, targetID):
        self.path = f'{filePath}/{targetID}.txt'
        self.PathID = os.path.split(self.path)[1].split('.')[0]
        self.GOChildrenPathIDList = []
        with open(self.path, 'r') as component:
            RectData = component.readlines()
            for dataLines in RectData:
                if 'm_GameObject' in dataLines:
                    dataIndex = RectData.index(dataLines)
                    GameObjectInfo = RectData[dataIndex + 1 : dataIndex + 3]
                    for info in GameObjectInfo:
                        if 'm_PathID' in info:
                            GameObjectPathID = info.split(' ')[1]
                            with open(f'{os.path.split(self.path)[0]}/{GameObjectPathID}.txt') as GameObjectData:
                                for info in GameObjectData.readlines():
                                    if 'm_PathID' in info:
                                        self.GOChildrenPathIDList.append(info.split(' ')[1])
                                    if 'm_Name' in info:
                                        RectName = info.split('"')[1]
                                        self.name = RectName
                                        break
                            break
                    break
    def Continue(self):
        self.ChildrenPathID = []
        if self.name != 'layers':
            for ChildrenPathIDs in self.GOChildrenPathIDList:
                with open(f'{os.path.split(self.path)[0]}/{ChildrenPathIDs}.txt') as component:
                    ChildrenData = component.readlines()
                    if 'MonoBehaviour' in ChildrenData[0]:
                        for MonoInfo in ChildrenData:
                            if 'mRawSpriteSize' in MonoInfo:
                                self.RawSize = self.GeneralDataProcess(MonoInfo)
                                break
                        break
        with open(self.path, 'r') as component:
            RectData = component.readlines()
            for dataLines in RectData:
                if 'm_LocalRotation' in dataLines:
                    dataIndex = RectData.index(dataLines)
                    TargetData = RectData[dataIndex + 1 : dataIndex + 5]
                    dataList = []
                    for info in TargetData:
                        dataList.append(Decimal(info.split(' ')[1]))
                    self.LocalRotation = dataList
                elif 'm_Father' in dataLines:
                    dataIndex = RectData.index(dataLines)
                    TargetInfo = RectData[dataIndex + 1 : dataIndex + 3]
                    for info in TargetInfo:
                        if 'm_PathID' in info:
                            FatherID = info.split(' ')[1]
                            self.FatherPathID = FatherID if FatherID != '0' else None
                elif 'm_PathID' in dataLines:
                    dataIndex = RectData.index(dataLines)
                    ChildrenHead = RectData[dataIndex - 2]
                    if 'data' in ChildrenHead:
                        self.ChildrenPathID.append(dataLines.split(' ')[1])
                elif 'm_LocalPosition' in dataLines:
                    self.LocalPosition = self.GeneralDataProcess(dataLines)
                elif 'm_LocalScale' in dataLines:
                    self.LocalScale = self.GeneralDataProcess(dataLines)
                elif 'm_AnchorMin' in dataLines:
                    self.AnchorMin = self.GeneralDataProcess(dataLines)
                elif 'm_AnchorMax' in dataLines:
                    self.AnchorMax = self.GeneralDataProcess(dataLines)
                elif 'm_AnchoredPosition' in dataLines:
                    self.AnchoredPosition = self.GeneralDataProcess(dataLines)
                elif 'm_SizeDelta' in dataLines:
                    self.SizeDelta = self.GeneralDataProcess(dataLines)
                elif 'm_Pivot' in dataLines:
                    self.Pivot = self.GeneralDataProcess(dataLines)
    def SetFatherRectObject(self, RectObject):
        self.__FatherRect = RectObject
        return 0
    def GetFatherRectObject(self):
        return self.__FatherRect
    def GeneralDataProcess(self, dataLine: str):
        dataList = []
        for data in dataLine.split('(')[1].split(')')[0].split(' '):
            dataList.append(Decimal(data))
        return dataList
    def CalculateRectSize(self):
        if self.__FatherRect == None:
            self.Size = self.SizeDelta
        else:
            self.Size = [
                Decimal(self.SizeDelta[0] + Decimal((self.AnchorMax[0] - self.AnchorMin[0]) * self.__FatherRect.Size[0])),
                Decimal(self.SizeDelta[1] + Decimal((self.AnchorMax[1] - self.AnchorMin[1]) * self.__FatherRect.Size[1]))
            ]
        return 0
def ExtractAssetBundle(abPath, Reflect):
    Reflect.Clear()
    abBasename = os.path.basename(abPath)
    dataPath = 'N/A'
    cacheFilesPath = f'./cache/{abBasename}'
    os.mkdir(cacheFilesPath)
    WebExtractInfo = os.popen(f'WebExtract {abPath}').readlines()
    Reflect.AppendText('Unpacking AssetBundle...\n')
    for i in WebExtractInfo:
        if 'creating folder' in i:
            dataPath = i.split("'")[1]
            break
    if dataPath == 'N/A':
        Reflect.AppendText("\nERROR: Can't read or not a Unity web file.\n")
        return 1
    for root, dirs, files in os.walk(dataPath):
        for fileName in files:
            CABPath = os.path.join(root, fileName)
    Reflect.AppendText('Reading unpacked CAB File...\n')
    a = os.popen(f'binary2text {CABPath}').read()
    Reflect.AppendText('Spliting AssetBundle data...\n')
    LastPathID = '0'
    dataLineList = []
    BaseClassID = '0'
    BaseRectPathID = '0'
    if not os.path.exists(f'{CABPath}.txt'):
        Reflect.AppendText("\nERROR: Invalid Unity web file.\n")
        rmtree(os.path.split(CABPath)[0])
        return 1
    with open(f'{CABPath}.txt', 'r') as abComponent:
        Reflect.AppendText('Creating cache files...\n')
        for dataLines in abComponent.readlines():
            if dataLines == '\n':
                continue
            if dataLines[:3] == 'ID:':
                PathID = dataLines.split(' ')[1]
                if LastPathID == '0':
                    LastPathID = PathID
                    dataLineList.append(dataLines.split(' ')[-1])
                if PathID != LastPathID:
                    with open(f'{cacheFilesPath}/{LastPathID}.txt', 'w') as cacheFile:
                        cacheFile.write(''.join(dataLineList))
                    dataLineList = [dataLines.split(' ')[-1]]
                    LastPathID = PathID
            elif LastPathID != '0':
                dataLineList.append(dataLines)
                if f'm_Name "{abBasename}" (string)' in dataLines:
                    BaseClassID = PathID
        with open(f'{cacheFilesPath}/{PathID}.txt', 'w') as cacheFile:
            cacheFile.write(''.join(dataLineList))
    rmtree(os.path.split(CABPath)[0])
    return cacheFilesPath, BaseClassID
class WorkFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent = None, title = '操作面板', size = (1318, 634), style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)
        self.Centre()
        FramePanel = wx.Panel(self)
        Sub_TaskFile = wx.StaticBox(FramePanel, label = '文件处理', pos = (16, 10), size = (384, 255))
        self.LoadFileButton = wx.Button(Sub_TaskFile, label = '导入文件', pos = (16, 22))
        TaskTitle = wx.StaticText(Sub_TaskFile, label = '当前任务:', pos = (112, 30))
        self.TaskLabel = wx.StaticText(Sub_TaskFile, label = '空闲中', pos = (170, 30))
        self.ProcessInfo = wx.TextCtrl(Sub_TaskFile, pos = (17, 66), size = (349, 170), style = wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_NO_VSCROLL)

        self.Sub_Painting = wx.StaticBox(FramePanel, label = '立绘导入', pos = (16, 273), size = (384, 255))
        self.LoadPaintingButton = wx.Button(self.Sub_Painting, label = '添加立绘', pos = (16, 22))
        NameTitle = wx.StaticText(self.Sub_Painting, label = '目标名称:', pos = (112, 30))
        self.NameLabel = wx.StaticText(self.Sub_Painting, label = 'N/A', pos = (170, 30))
        self.NeedsNameBox = wx.ListBox(self.Sub_Painting, pos = (17, 66), size = (349, 170), style = wx.LB_SINGLE | wx.LB_HSCROLL | wx.LB_OWNERDRAW)
        self.Sub_Painting.Disable()
        
        self.PreviewBook = wx.Notebook(FramePanel, pos = (416, 10), size = (872, 570))
        self.PreviewPanel = wx.Panel(self.PreviewBook)
        self.PreviewPanel.SetBackgroundColour('#FFFFFF')
        self.InitImg = Image.new('RGBA', (864, 540), (255, 255, 255, 255))
        TextFont = ImageFont.truetype('arialbd', 54)
        DrawImage = ImageDraw.Draw(self.InitImg)
        DrawImage.text((330, 197), 'Preview\n  is not\navalible', fill = (116, 116, 116), font = TextFont)
        InitImgData = self.InitImg.convert('RGB').tobytes()
        self.InitImgPre = wx.Bitmap(img = wx.Image(width = 864, height = 540, data = InitImgData))
        self.PreviewImage = self.InitImgPre
        self.PreviewBook.AddPage(self.PreviewPanel, 'Preview')
        self.PreviewPanel.Refresh()
        self.SaveButton = wx.Button(FramePanel, label = '保存', pos = (15, 544), size = (186, 36))
        self.SaveButton.Disable()
        self.OpenFolderButton = wx.Button(FramePanel, label = '打开文件夹', pos = (215, 544), size = (186, 36))

        self.PreviewPanel.Bind(wx.EVT_ERASE_BACKGROUND, self.DoNothing)
        self.PreviewPanel.Bind(wx.EVT_PAINT, self.RefreshPreview)
        self.LoadFileButton.Bind(wx.EVT_BUTTON, self.LoadFile)
        self.LoadPaintingButton.Bind(wx.EVT_BUTTON, self.LoadPainting)
        self.NeedsNameBox.Bind(wx.EVT_LISTBOX, self.ShowSelectedName)
        self.SaveButton.Bind(wx.EVT_BUTTON, self.Saveto)
        self.OpenFolderButton.Bind(wx.EVT_BUTTON, self.OpenFolder)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
    def LoadFile(self, event):
        fileDia = wx.FileDialog(self, message = '导入文件', defaultDir = PaintingConfigs.filesPath)
        if fileDia.ShowModal() == wx.ID_OK:
            self.TaskLabel.SetLabel(fileDia.GetFilename())
            filePath = fileDia.GetPath()
            PaintingConfigs.Update(p1 = os.path.split(filePath)[0])
            return self.Painting(filePath)
    def Painting(self, abPath):
        self.NameLabel.SetLabel('N/A')
        self.NeedsNameBox.Clear()
        self.Sub_Painting.Disable()
        self.SaveButton.Disable()
        PageCount = self.PreviewBook.GetPageCount()
        if PageCount >= 2:
            for j in range(1, PageCount):
                self.PreviewBook.DeletePage(1)
        self.PreviewImage = self.InitImgPre
        self.PreviewPanel.Refresh()
        try: cacheFilesPath, BaseClassID = ExtractAssetBundle(abPath, self.ProcessInfo)
        except: return 1
        self.ProcessInfo.AppendText('Building RectTransform Object...\n')
        self.RectList = []
        self.RectPathIDList = []
        self.RectNameList = []
        self.RectRawSizeList = []
        self.RectStretchSizeList = []
        self.ChildrenRectNameList = []
        self.TempChoiceList = []
        with open(f'{cacheFilesPath}/{BaseClassID}.txt', 'r') as BaseClass:
            for BaseDataLines in BaseClass.readlines():
                if 'm_PathID' in BaseDataLines:
                    ChildPathID = BaseDataLines.split(' ')[1]
                    with open(f'{cacheFilesPath}/{ChildPathID}.txt', 'r') as ChildClass:
                        if 'RectTransform' in ChildClass.readlines()[0]:
                            BaseRectPathID = ChildPathID
                            break
        BaseRect = RectTransform(cacheFilesPath, BaseRectPathID)
        BaseRect.Continue()
        self.RectList.append(BaseRect)
        self.RectPathIDList.append(BaseRect.PathID)
        self.RectNameList.append(BaseRect.name)
        for LayersPathID in BaseRect.ChildrenPathID:
            LayersRect = RectTransform(cacheFilesPath, LayersPathID)
            if LayersRect.name == 'layers':
                LayersRect.Continue()
                break
        if LayersRect.name != 'layers':
            self.ProcessInfo.AppendText('\nERROR: No needed or unable to analyze.')
            return 1
        self.RectList.append(LayersRect)
        self.RectPathIDList.append(LayersRect.PathID)
        self.RectNameList.append(LayersRect.name)
        for ChildrenPathID in LayersRect.ChildrenPathID:
            ChildrenRect = RectTransform(cacheFilesPath, ChildrenPathID)
            ChildrenRect.Continue()
            self.RectList.append(ChildrenRect)
            self.RectPathIDList.append(ChildrenRect.PathID)
            self.RectNameList.append(ChildrenRect.name)
            self.ChildrenRectNameList.append(ChildrenRect.name)
        RectPathIDDict = dict(zip(self.RectPathIDList, self.RectList))
        RectNameDict = dict(zip(self.RectNameList, self.RectList))
        for RectObject in self.RectList:
            FatherRect = RectPathIDDict.get(RectObject.FatherPathID) if RectObject.FatherPathID != None else None
            RectObject.SetFatherRectObject(FatherRect)
            RectObject.CalculateRectSize()
            if RectObject.name == 'layers':
                LayersRect = RectObject
            else:
                self.RectRawSizeList.append(RectObject.RawSize)
                self.RectStretchSizeList.append(RectObject.Size)
        BaseRect = LayersRect.GetFatherRectObject()
        self.ProcessInfo.AppendText('Calculating coordinates...\n')
        PastePointsList = []
        LayersOrigin = [
            Decimal(Decimal((LayersRect.AnchorMax[0] - LayersRect.AnchorMin[0]) * BaseRect.Size[0] * LayersRect.Pivot[0]) + Decimal(LayersRect.AnchorMin[0] * BaseRect.Size[0]) + LayersRect.AnchoredPosition[0] - Decimal(LayersRect.Size[0] * LayersRect.Pivot[0])),
            Decimal(Decimal((LayersRect.AnchorMax[1] - LayersRect.AnchorMin[1]) * BaseRect.Size[1] * LayersRect.Pivot[1]) + Decimal(LayersRect.AnchorMin[1] * BaseRect.Size[1]) + LayersRect.AnchoredPosition[1] - Decimal(LayersRect.Size[1] * LayersRect.Pivot[1]))
        ]
        for ChildrenRectName in self.ChildrenRectNameList:
            ChildrenRect = RectNameDict.get(ChildrenRectName)
            PastePoint = (
                round(Decimal(Decimal((ChildrenRect.AnchorMax[0] - ChildrenRect.AnchorMin[0]) * LayersRect.Size[0] * ChildrenRect.Pivot[0]) + Decimal(ChildrenRect.AnchorMin[0] * LayersRect.Size[0]) + ChildrenRect.AnchoredPosition[0] + LayersOrigin[0] - Decimal(ChildrenRect.Size[0] * ChildrenRect.Pivot[0]))) + 1,
                round(Decimal(BaseRect.Size[1] - (Decimal((ChildrenRect.AnchorMax[1] - ChildrenRect.AnchorMin[1]) * LayersRect.Size[1] * ChildrenRect.Pivot[1]) + Decimal(ChildrenRect.AnchorMin[0] * LayersRect.Size[1]) + ChildrenRect.AnchoredPosition[1] + LayersOrigin[1] + Decimal(ChildrenRect.Size[1] * (Decimal('1') - ChildrenRect.Pivot[1]))))) - 1
            )
            PastePointsList.append(PastePoint)
        self.RectNameList.remove('layers')
        self.RectNamePointDict = dict(zip(self.ChildrenRectNameList, PastePointsList))
        self.RectNameRawSizeDict = dict(zip(self.RectNameList, self.RectRawSizeList))
        self.RectNameStretchSizeDict = dict(zip(self.RectNameList, self.RectStretchSizeList))
        self.PaintingList = self.RectNameList[:]
        self.CheckList = [False for l in range(0, len(self.RectNameList))]
        self.ProcessInfo.AppendText('\nDone! Please load painting pictures.\n')
        return self.ActivePainting()
    def ActivePainting(self):
        self.Sub_Painting.Enable()
        self.NeedsNameBox.SetItems(self.RectNameList)
        self.NeedsNameBox.SetSelection(0)
        self.NeedsName = self.NeedsNameBox.GetStringSelection()
        self.NameLabel.SetLabel(self.NeedsName)
        self.WildCard = f'Required Files ({PaintingConfigs.wildCard})|{PaintingConfigs.wildCard}'.replace(r'{name}', self.NeedsName)
        return 0
    def LoadPainting(self, event):
        paintingDia = wx.FileDialog(self, message = '导入立绘', defaultDir = PaintingConfigs.paintingPath, wildcard = self.WildCard)
        if paintingDia.ShowModal() == wx.ID_OK:
            self.PreviewBook.SetSelection(0)
            PaintingPath = paintingDia.GetPath()
            Painting = Image.open(PaintingPath)
            TargetIndex = self.RectNameList.index(self.NeedsName)
            Expend = Image.new('RGBA', self.RectNameRawSizeDict.get(self.NeedsName), (0, 0, 0, 0))
            Painting = Painting.transpose(Image.FLIP_TOP_BOTTOM)
            Expend.paste(Painting, (0, 0))
            Painting = Expend.transpose(Image.FLIP_TOP_BOTTOM)
            Painting = Painting.resize(self.RectNameStretchSizeDict.get(self.NeedsName), Image.ANTIALIAS)
            self.PaintingList[TargetIndex] = Painting
            self.CheckList[TargetIndex] = True
            PageImage = wx.StaticBitmap(self.PreviewBook, bitmap = self.ReleasePreview(Painting), pos = (-64, -64))
            for k in range(1, self.PreviewBook.GetPageCount()):
                if self.PreviewBook.GetPageText(k) == self.NeedsName:
                    self.PreviewBook.DeletePage(k)
                    self.PreviewBook.InsertPage(k, PageImage, self.NeedsName)
                    break
            else:
                self.PreviewBook.AddPage(PageImage, self.NeedsName)
            self.NeedsNameBox.SetItemForegroundColour(TargetIndex, 'blue')
            if self.NeedsName != self.RectNameList[-1]:
                TargetIndex += 1
                self.NeedsNameBox.SetSelection(TargetIndex)
                self.ShowSelectedName(None)
            PaintingConfigs.Update(p2 = os.path.split(PaintingPath)[0])
            return self.GroupPainting()
    def ShowSelectedName(self, event):
        self.NeedsName = self.NeedsNameBox.GetStringSelection()
        self.NameLabel.SetLabel(self.NeedsName)
        self.WildCard = f'Required Files ({PaintingConfigs.wildCard})|{PaintingConfigs.wildCard}'.replace(r'{name}', self.NeedsName)
        return 0
    def GroupPainting(self):
        RectNamePicDict = dict(zip(self.RectNameList, self.PaintingList))
        self.GroupedPainting = self.InitImg
        for RectName in self.RectNameList:
            Painting = RectNamePicDict.get(RectName)
            if isinstance(Painting, Image.Image):
                UsedPainting = Painting.copy()
                RectNumber = self.RectNameList.index(RectName)
                if RectNumber == 0:
                    self.GroupedPainting = Image.new('RGBA', UsedPainting.size, (0, 0, 0, 0))
                    self.GroupedPainting.paste(UsedPainting, (0, 0))
                else:
                    Blank = Image.new('RGBA', self.GroupedPainting.size, (0, 0, 0, 0))
                    Blank.paste(UsedPainting, self.RectNamePointDict.get(RectName))
                    self.GroupedPainting = Image.alpha_composite(self.GroupedPainting, Blank)
            else:
                break
        if len(set(self.CheckList)) == 1 and set(self.CheckList) == {True}:
            self.SaveButton.Enable()
        self.PreviewImage = self.ReleasePreview(self.GroupedPainting)
        self.PreviewPanel.Refresh()
        return 0
    def ReleasePreview(self, imgObject):
        Blank = Image.new('RGBA', (864, 540), (0, 0, 0, 0))
        width = round(Decimal(imgObject.size[0] / imgObject.size[1] * 540))
        height = 540
        if width > 864:
            width = 864
            height = round(Decimal(imgObject.size[1] / imgObject.size[0] * 864))
        Example = imgObject.resize((width, height), Image.ANTIALIAS)
        Blank.paste(Example, (round((864 - width) / 2), round((540 - height) / 2)), Example)
        return wx.Bitmap(img = wx.Image(width = 864, height = 540, data = Blank.convert('RGB').tobytes(), alpha = Blank.tobytes()[3::4]))
    def RefreshPreview(self, event):
        buffer = wx.BufferedPaintDC(self.PreviewPanel)
        buffer.Clear()
        try:
            buffer.DrawBitmap(self.PreviewImage, x = 0, y = 0)
        except:
            pass
        return 0
    def Saveto(self, event):
        self.GroupedPainting.save(f'{PaintingConfigs.paintingPath}/{self.RectNameList[0]}_group.png')
        return 0
    def OpenFolder(self, event):
        os.popen(f'start explorer {PaintingConfigs.paintingPath}')
        return 0
    def DoNothing(self, event):
        return 0
    def OnClose(self, event):
        self.Destroy()
        for cacheFolder in os.listdir('./cache'):
            rmtree(f'./cache/{cacheFolder}')
        PaintingConfigs.UpdateFile()
        PaintingFaceConfigs.UpdateFile()
        return 0

with open('ALPAConfigs.yml', encoding = 'utf-8') as yamlFile:
    configFile = yaml.safe_load(yamlFile)
PaintingConfigs = ConfigSet('painting')
PaintingFaceConfigs = ConfigSet('paintingface')
MainApp = wx.App()
CtrlFrame = WorkFrame()
CtrlFrame.Show()
MainApp.MainLoop()