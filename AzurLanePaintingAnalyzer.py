# -*- coding: utf-8 -*-
from PIL import Image, ImageFont, ImageDraw
from shutil import rmtree, copy
from decimal import Decimal
import tex2img
import yaml
import os
import wx

class PaintingSetting:
    def __init__(self, setting):
        self.filesPath = setting.get('importFilesPath')
        self.paintingPath = setting.get('importPaintingPath')
        self.wildCard = setting.get('wildCard')
    def Update(self, p1 = None, p2 = None):
        self.filesPath = self.filesPath if p1 == None else p1
        self.paintingPath = self.paintingPath if p2 == None else p2
        return 0
    def FileForm(self):
        updateDict = {
            'painting': {
                'importFilesPath': self.filesPath,
                'importPaintingPath': self.paintingPath,
                'wildCard': self.wildCard
            }
        }
        return updateDict
class PaintingfaceSetting:
    def __init__(self, setting):
        self.IsCorrection = setting.get('ApplyCorrection')
        self.filesPath = setting.get('importFilesPath')
        self.face2DPath = setting.get('importFace2DPath')
        self.faceFilePath = setting.get('importFaceFilePath')
        self.wildCard2D = setting.get('wildCard_2D')
        self.wildCardFile = setting.get('wildCard_File')
    def Update(self, pf1 = None, pf2 = None, pf3 = None):
        self.filesPath = self.filesPath if pf1 == None else pf1
        self.face2DPath = self.face2DPath if pf2 == None else pf2
        self.faceFilePath = self.faceFilePath if pf3 == None else pf3
        return 0
    def FileForm(self):
        updateDict = {
            'paintingface': {
                'ApplyCorrection': self.IsCorrection,
                'importFilesPath': self.filesPath,
                'importFace2DPath': self.face2DPath,
                'importFaceFilePath': self.faceFilePath,
                'wildCard_2D': self.wildCard2D,
                'wildCard_File': self.wildCardFile
            }
        }
        return updateDict
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
                Decimal(self.SizeDelta[0] + (self.AnchorMax[0] - self.AnchorMin[0]) * self.__FatherRect.Size[0]),
                Decimal(self.SizeDelta[1] + (self.AnchorMax[1] - self.AnchorMin[1]) * self.__FatherRect.Size[1])
            ]
        return 0
def ExtractAssetBundle(ABPath, cacheSavePath, Reflect, Mode, InitBaseClassID = '0'):
    Reflect.Clear()
    abBasename = os.path.basename(ABPath)
    dataPath = 'N/A'
    WebExtractInfo = os.popen(f'WebExtract {ABPath}').readlines()
    Reflect.AppendText('Unpacking AssetBundle...\n')
    for i in WebExtractInfo:
        if 'creating folder' in i:
            dataPath = i.split("'")[1]
            break
    if dataPath == 'N/A':
        Reflect.AppendText("\nERROR: Can't read or not a Unity web file.\n")
        return -1
    FileList = []
    SuffixList = []
    for root, dirs, files in os.walk(dataPath):
        for fileName in files:
            CABFile = os.path.join(root, fileName)
            FileList.append(CABFile)
            suffix = os.path.splitext(CABFile)[1]
            SuffixList.append(suffix)
            if suffix == '':
                CABPath = CABFile
            elif suffix == '.resS':
                resSPath = CABFile
    if ((Mode == 'TextAsset' and len(set(SuffixList)) != 1) or
        (Mode == 'Texture2D' and not '.resS' in set(SuffixList))):
        Reflect.AppendText("\nERROR: Invalid Unity web file.\n")
        rmtree(os.path.split(CABFile)[0])
        return -1
    Reflect.AppendText('Reading unpacked CAB File...\n')
    a = os.popen(f'binary2text {CABPath}').read()
    LastPathID = '0'
    dataLineList = []
    BaseClassID = InitBaseClassID
    Reflect.AppendText('Spliting AssetBundle data...\n')
    with open(f'{CABPath}.txt', 'r') as abComponent:
        Reflect.AppendText('Creating cache files...\n')
        for dataLines in abComponent.readlines():
            if dataLines == '\n':
                continue
            elif dataLines[:3] == 'ID:':
                PathID = dataLines.split(' ')[1]
                AssetType = dataLines.split(' ')[-1]
                if LastPathID == '0':
                    LastPathID = PathID
                    dataLineList.append(dataLines.split(' ')[-1])
                if PathID != LastPathID:
                    with open(f'{cacheSavePath}/{LastPathID}.txt', 'w') as cacheFile:
                        cacheFile.write(''.join(dataLineList))
                    dataLineList = [dataLines.split(' ')[-1]]
                    LastPathID = PathID
            elif LastPathID != '0':
                dataLineList.append(dataLines)
                if 'GameObject' in AssetType:
                    if ((f'm_Name "{abBasename}" (string)' in dataLines) or
                        (f'm_Name "{abBasename.upper()}" (string)' in dataLines)):
                        BaseClassID = PathID
        with open(f'{cacheSavePath}/{PathID}.txt', 'w') as cacheFile:
            cacheFile.write(''.join(dataLineList))
    if Mode == 'Texture2D':
        returnValue = copy(resSPath, cacheSavePath)
    elif Mode == 'TextAsset':
        if BaseClassID == '0':
            Reflect.AppendText('\nERROR: Not original file name.\n')
            returnValue = -1
        else:
            returnValue = BaseClassID
    rmtree(os.path.split(CABPath)[0])
    return returnValue
def ReleasePreview(imgObject):
        Blank = Image.new('RGBA', (864, 540), (0, 0, 0, 0))
        width = round(Decimal(imgObject.size[0] / imgObject.size[1] * 540))
        height = 540
        if width > 864:
            width = 864
            height = round(Decimal(imgObject.size[1] / imgObject.size[0] * 864))
        Example = imgObject.resize((width, height), Image.ANTIALIAS)
        Blank.paste(Example, (round((864 - width) / 2), round((540 - height) / 2)))
        return wx.Bitmap(img = wx.Image(width = 864, height = 540, data = Blank.convert('RGB').tobytes(), alpha = Blank.tobytes()[3::4]))
class PaintingFrame(wx.Panel):
    def __init__(self, Parent):
        super().__init__(Parent)
        Sub_TaskFile = wx.StaticBox(self, label = '文件处理', pos = (16, 10), size = (384, 255))
        self.LoadFileButton = wx.Button(Sub_TaskFile, label = '导入文件', pos = (16, 22))
        TaskTitle = wx.StaticText(Sub_TaskFile, label = '当前任务:', pos = (112, 30))
        self.TaskLabel = wx.StaticText(Sub_TaskFile, label = '空闲中', pos = (170, 30))
        self.ProcessInfo = wx.TextCtrl(Sub_TaskFile, pos = (17, 66), size = (349, 170), style = wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_NO_VSCROLL)

        self.Sub_Painting = wx.StaticBox(self, label = '立绘导入', pos = (16, 273), size = (384, 255))
        self.LoadPaintingButton = wx.Button(self.Sub_Painting, label = '添加立绘', pos = (16, 22))
        NameTitle = wx.StaticText(self.Sub_Painting, label = '目标名称:', pos = (112, 30))
        self.NameLabel = wx.StaticText(self.Sub_Painting, label = 'N/A', pos = (170, 30))
        self.NeedsNameBox = wx.ListBox(self.Sub_Painting, pos = (17, 66), size = (349, 170), style = wx.LB_SINGLE | wx.LB_HSCROLL | wx.LB_OWNERDRAW)
        self.Sub_Painting.Disable()
        
        self.PreviewBook = wx.Notebook(self, pos = (416, 10), size = (872, 570))
        self.PreviewPanel = wx.Panel(self.PreviewBook)
        self.PreviewPanel.SetBackgroundColour('#FFFFFF')
        self.PreviewImage = InitImgPre
        self.PreviewBook.AddPage(self.PreviewPanel, 'Preview')
        self.PreviewPanel.Refresh()
        self.SaveButton = wx.Button(self, label = '保存', pos = (15, 544), size = (186, 36))
        self.SaveButton.Disable()
        self.OpenFolderButton = wx.Button(self, label = '打开文件夹', pos = (215, 544), size = (186, 36))

        self.PreviewPanel.Bind(wx.EVT_ERASE_BACKGROUND, self.DoNothing)
        self.PreviewPanel.Bind(wx.EVT_PAINT, self.RefreshPreview)
        self.LoadFileButton.Bind(wx.EVT_BUTTON, self.LoadFile)
        self.LoadPaintingButton.Bind(wx.EVT_BUTTON, self.LoadPainting)
        self.NeedsNameBox.Bind(wx.EVT_LISTBOX, self.ShowSelectedName)
        self.SaveButton.Bind(wx.EVT_BUTTON, self.Saveto)
        self.OpenFolderButton.Bind(wx.EVT_BUTTON, self.OpenFolder)       
    def LoadFile(self, event):
        fileDia = wx.FileDialog(self, message = '导入文件', defaultDir = PaintingConfigs.filesPath)
        if fileDia.ShowModal() == wx.ID_OK:
            self.TaskLabel.SetLabel(fileDia.GetFilename())
            filePath = fileDia.GetPath()
            PaintingConfigs.Update(p1 = os.path.split(filePath)[0])
            return self.Painting(filePath)
    def Painting(self, ABPath):
        self.NameLabel.SetLabel('N/A')
        self.NeedsNameBox.Clear()
        self.Sub_Painting.Disable()
        self.SaveButton.Disable()
        PageCount = self.PreviewBook.GetPageCount()
        if PageCount >= 2:
            for j in range(1, PageCount):
                self.PreviewBook.DeletePage(1)
        self.PreviewImage = InitImgPre
        self.PreviewPanel.Refresh()
        RootPath = './cache/painting'
        if os.path.exists(RootPath):
            for cacheFolder in os.listdir(RootPath):
                rmtree(f'{RootPath}/{cacheFolder}')
        if not os.path.exists(RootPath): os.mkdir(RootPath)
        self.cacheFilesPath = f'{RootPath}/{os.path.basename(ABPath)}'
        os.mkdir(self.cacheFilesPath)
        BaseClassID = ExtractAssetBundle(ABPath, self.cacheFilesPath, self.ProcessInfo, 'TextAsset')
        if BaseClassID == -1:
            return -1
        self.ProcessInfo.AppendText('Building RectTransform Object...\n')
        self.RectList = []
        self.RectPathIDList = []
        self.RectNameList = []
        self.RectRawSizeList = []
        self.RectStretchSizeList = []
        self.RectLocalScaleList = []
        self.ChildrenRectNameList = []
        self.PastePointsList = []
        self.CacheRectList = []
        with open(f'{self.cacheFilesPath}/{BaseClassID}.txt', 'r') as BaseClass:
            for BaseDataLines in BaseClass.readlines():
                if 'm_PathID' in BaseDataLines:
                    ChildPathID = BaseDataLines.split(' ')[1]
                    with open(f'{self.cacheFilesPath}/{ChildPathID}.txt', 'r') as ChildClass:
                        if 'RectTransform' in ChildClass.readlines()[0]:
                            BaseRectPathID = ChildPathID
                            break
        BaseRect = RectTransform(self.cacheFilesPath, BaseRectPathID)
        BaseRect.Continue()
        BaseRect.LocalScale = [Decimal('1'), Decimal('1'), Decimal('1')]
        self.RectList.append(BaseRect)
        self.RectPathIDList.append(BaseRect.PathID)
        self.RectNameList.append(BaseRect.name)
        for LayersPathID in BaseRect.ChildrenPathID:
            LayersRect = RectTransform(self.cacheFilesPath, LayersPathID)
            if LayersRect.name == 'layers':
                LayersRect.Continue()
                break
            elif LayersRect.name == 'paint':
                self.CacheRectList.append(LayersRect)
        if LayersRect.name != 'layers':
            if not self.CacheRectList:
                self.ProcessInfo.AppendText('\nERROR: No needed or unable to analyze.')
                return -1
            else:
                LayersRect = self.CacheRectList[0]
                LayersRect.Continue()
        self.RectList.append(LayersRect)
        self.RectPathIDList.append(LayersRect.PathID)
        self.RectNameList.append(LayersRect.name)
        for ChildrenPathID in LayersRect.ChildrenPathID:
            ChildrenRect = RectTransform(self.cacheFilesPath, ChildrenPathID)
            ChildrenRect.Continue()
            self.RectList.append(ChildrenRect)
            self.RectPathIDList.append(ChildrenRect.PathID)
            self.RectNameList.append(ChildrenRect.name)
            self.ChildrenRectNameList.append(ChildrenRect.name)
        RectPathIDDict = dict(zip(self.RectPathIDList, self.RectList))
        self.RectNameDict = dict(zip(self.RectNameList, self.RectList))
        for RectObject in self.RectList:
            FatherRect = RectPathIDDict.get(RectObject.FatherPathID) if RectObject.FatherPathID != None else None
            RectObject.SetFatherRectObject(FatherRect)
            RectObject.CalculateRectSize()
            if RectObject.name != 'layers':
                self.RectRawSizeList.append(RectObject.RawSize)
                self.RectStretchSizeList.append(RectObject.Size)
                self.RectLocalScaleList.append(RectObject.LocalScale)
        self.ProcessInfo.AppendText('Calculating coordinates...\n')
        if LayersRect.name == 'layers':
            LayersOrigin = [
                Decimal((LayersRect.AnchorMax[0] - LayersRect.AnchorMin[0]) * BaseRect.Size[0] * LayersRect.Pivot[0] + LayersRect.AnchorMin[0] * BaseRect.Size[0] + LayersRect.AnchoredPosition[0] - LayersRect.Size[0] * LayersRect.Pivot[0] * LayersRect.LocalScale[0]),
                Decimal((LayersRect.AnchorMax[1] - LayersRect.AnchorMin[1]) * BaseRect.Size[1] * LayersRect.Pivot[1] + LayersRect.AnchorMin[1] * BaseRect.Size[1] + LayersRect.AnchoredPosition[1] - LayersRect.Size[1] * LayersRect.Pivot[1] * LayersRect.LocalScale[1])
            ]
            for ChildrenRectName in self.ChildrenRectNameList:
                ChildrenRect = self.RectNameDict.get(ChildrenRectName)
                PastePoint = [
                    round(Decimal((ChildrenRect.AnchorMax[0] - ChildrenRect.AnchorMin[0]) * LayersRect.Size[0] * ChildrenRect.Pivot[0] + ChildrenRect.AnchorMin[0] * LayersRect.Size[0] + ChildrenRect.AnchoredPosition[0] + LayersOrigin[0] - ChildrenRect.Size[0] * ChildrenRect.Pivot[0] * ChildrenRect.LocalScale[0])) + 1,
                    round(Decimal((ChildrenRect.AnchorMax[1] - ChildrenRect.AnchorMin[1]) * LayersRect.Size[1] * ChildrenRect.Pivot[1] + ChildrenRect.AnchorMin[1] * LayersRect.Size[1] + ChildrenRect.AnchoredPosition[1] + LayersOrigin[1] - ChildrenRect.Size[1] * ChildrenRect.Pivot[1] * ChildrenRect.LocalScale[1])) + 1
                ]
                self.PastePointsList.append(PastePoint)
            self.RectNameList.remove('layers')
        elif LayersRect.name == 'paint':
            LayersRect.name = f'{BaseRect.name}_p'
            self.RectNameList[self.RectNameList.index('paint')] = LayersRect.name
            self.RectNameDict = dict(zip(self.RectNameList, self.RectList))
            self.ChildrenRectNameList.append(LayersRect.name)
            PastePoint = [
                round(Decimal((LayersRect.AnchorMax[0] - LayersRect.AnchorMin[0]) * BaseRect.Size[0] * LayersRect.Pivot[0] + LayersRect.AnchorMin[0] * BaseRect.Size[0] + LayersRect.AnchoredPosition[0] - LayersRect.Size[0] * LayersRect.Pivot[0] * LayersRect.LocalScale[0])) + 1,
                round(Decimal((LayersRect.AnchorMax[1] - LayersRect.AnchorMin[1]) * BaseRect.Size[1] * LayersRect.Pivot[1] + LayersRect.AnchorMin[1] * BaseRect.Size[1] + LayersRect.AnchoredPosition[1] - LayersRect.Size[1] * LayersRect.Pivot[1] * LayersRect.LocalScale[1])) + 1
            ]
            self.PastePointsList.append(PastePoint)
        self.ExPixelList = [0, 0, 0, 0]
        PointX = []
        PointY = []
        for point in self.PastePointsList:
            PointX.append(point[0])
            PointY.append(point[1])
        self.ExPixelList[0] = abs(min(PointX)) if min(PointX) < 0 else 0
        self.ExPixelList[3] = abs(min(PointY)) if min(PointY) < 0 else 0
        RectNameRawPointDict = dict(zip(self.ChildrenRectNameList, self.PastePointsList))
        PointX = []
        PointY = []
        for ChildName in self.ChildrenRectNameList:
            ChildRect = self.RectNameDict.get(ChildName)
            point = RectNameRawPointDict.get(ChildName)
            PointX.append(round(ChildRect.Size[0] * ChildRect.LocalScale[0] + point[0] - BaseRect.Size[0]))
            PointY.append(round(ChildRect.Size[1] * ChildRect.LocalScale[1] + point[1] - BaseRect.Size[1]))
        self.ExPixelList[2] = max(PointX) if max(PointX) > 0 else 0
        self.ExPixelList[1] = max(PointY) if max(PointY) > 0 else 0
        for point in self.PastePointsList:
            index = self.PastePointsList.index(point)
            point[0] += self.ExPixelList[0]
            point[1] += self.ExPixelList[3]
            self.PastePointsList[index] = tuple(point)
        self.FileName = f'{PaintingConfigs.paintingPath}\{self.RectNameList[0]}_group.png'
        self.RectNamePointDict = dict(zip(self.ChildrenRectNameList, self.PastePointsList))
        self.RectNameRawSizeDict = dict(zip(self.RectNameList, self.RectRawSizeList))
        self.RectNameStretchSizeDict = dict(zip(self.RectNameList, self.RectStretchSizeList))
        self.RectNameScaleDict = dict(zip(self.RectNameList, self.RectLocalScaleList))
        self.PaintingList = self.RectNameList[:]
        self.CheckList = [False for l in range(0, len(self.RectNameList))]
        self.ProcessInfo.AppendText('\nDone! Please load painting.\n')
        return self.ActivePainting()
    def ActivePainting(self):
        self.Sub_Painting.Enable()
        self.NeedsNameBox.SetItems(self.RectNameList)
        self.NeedsNameBox.SetSelection(0)
        self.NeedsName = self.NeedsNameBox.GetStringSelection()
        self.NameLabel.SetLabel(self.NeedsName)
        self.WildCard = f'Required Files ({PaintingConfigs.wildCard})|{PaintingConfigs.wildCard}|All Paintings (*.png)|*.png'.replace(r'{name}', self.NeedsName)
        return 0
    def LoadPainting(self, event):
        paintingDia = wx.FileDialog(self, message = '导入立绘', defaultDir = PaintingConfigs.paintingPath, wildcard = self.WildCard)
        if paintingDia.ShowModal() == wx.ID_OK:
            self.PreviewBook.SetSelection(0)
            PaintingPath = paintingDia.GetPath()
            Painting = Image.open(PaintingPath)
            TargetIndex = self.RectNameList.index(self.NeedsName)
            RawSizeData = self.RectNameRawSizeDict.get(self.NeedsName)
            RawSize = [RawSizeData[0] if RawSizeData[0] >= Painting.size[0] else Painting.size[0], RawSizeData[1] if RawSizeData[1] >= Painting.size[1] else Painting.size[1]]
            Extend = Image.new('RGBA', tuple(RawSize), (0, 0, 0, 0))
            Painting = Painting.transpose(Image.FLIP_TOP_BOTTOM)
            Extend.paste(Painting, (0, 0))
            Painting = Extend.transpose(Image.FLIP_TOP_BOTTOM)
            SizeData = self.RectNameStretchSizeDict.get(self.NeedsName)
            StretchSize = [SizeData[0] if SizeData[0] >= Painting.size[0] else Painting.size[0], SizeData[1] if SizeData[1] >= Painting.size[1] else Painting.size[1]]
            Painting = Painting.resize(tuple(StretchSize), Image.ANTIALIAS)
            PaintingScale = self.RectNameScaleDict.get(self.NeedsName)
            Painting = Painting.resize((round(Decimal(Painting.size[0] * PaintingScale[0])), round(Decimal(Painting.size[1] * PaintingScale[1]))), Image.ANTIALIAS)
            if TargetIndex == 0:
                Extend = Image.new('RGBA', (Painting.size[0] + self.ExPixelList[0] + self.ExPixelList[2], Painting.size[1] + self.ExPixelList[1] + self.ExPixelList[3]), (0, 0, 0, 0))
                Extend.paste(Painting, (self.ExPixelList[0], self.ExPixelList[1]))
                Painting = Extend
            self.PaintingList[TargetIndex] = Painting
            self.CheckList[TargetIndex] = True
            PageImage = wx.StaticBitmap(self.PreviewBook, bitmap = ReleasePreview(Painting), pos = (-64, -64))
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
            self.FileName = f'{PaintingConfigs.paintingPath}\{self.RectNameList[0]}_group.png'
            return self.GroupPainting()
    def ShowSelectedName(self, event):
        self.NeedsName = self.NeedsNameBox.GetStringSelection()
        self.NameLabel.SetLabel(self.NeedsName)
        self.WildCard = f'Required Files ({PaintingConfigs.wildCard})|{PaintingConfigs.wildCard}|All Paintings (*.png)|*.png'.replace(r'{name}', self.NeedsName)
        return 0
    def GroupPainting(self):
        RectNamePicDict = dict(zip(self.RectNameList, self.PaintingList))
        self.GroupedPainting = InitImg
        for RectName in self.RectNameList:
            Painting = RectNamePicDict.get(RectName)
            if isinstance(Painting, Image.Image):
                UsedPainting = Painting.copy()
                RectNumber = self.RectNameList.index(RectName)
                if RectNumber == 0:
                    self.GroupedPainting = Image.new('RGBA', UsedPainting.size, (0, 0, 0, 0))
                    self.GroupedPainting.paste(UsedPainting, (0, 0))
                else:
                    self.GroupedPainting = self.GroupedPainting.transpose(Image.FLIP_TOP_BOTTOM)
                    UsedPainting = UsedPainting.transpose(Image.FLIP_TOP_BOTTOM)
                    Blank = Image.new('RGBA', self.GroupedPainting.size, (0, 0, 0, 0))
                    Blank.paste(UsedPainting, self.RectNamePointDict.get(RectName))
                    self.GroupedPainting = Image.alpha_composite(self.GroupedPainting, Blank)
                    self.GroupedPainting = self.GroupedPainting.transpose(Image.FLIP_TOP_BOTTOM)
            else:
                break
        if len(set(self.CheckList)) == 1 and set(self.CheckList) == {True}:
            self.SaveButton.Enable()
        self.PreviewImage = ReleasePreview(self.GroupedPainting)
        self.PreviewPanel.Refresh()
        return 0
    def RefreshPreview(self, event):
        buffer = wx.BufferedPaintDC(self.PreviewPanel)
        buffer.Clear()
        try:
            buffer.DrawBitmap(self.PreviewImage, x = 0, y = 0)
        except:
            pass
        return 0
    def Saveto(self, event):
        self.GroupedPainting.save(self.FileName)
        return 0
    def OpenFolder(self, event):
        try:
            if not os.path.exists(self.FileName):
                os.popen(f'explorer {PaintingConfigs.paintingPath}')
            else:
                os.popen(f'explorer /select,"{self.FileName}"')
        except:
            os.popen(f'explorer {PaintingConfigs.paintingPath}')
        return 0
    def DoNothing(self, event):
        return 0 
class PaintingfaceFrame(wx.Panel):
    def __init__(self, Parent):
        super().__init__(Parent)
        Sub_TaskFile = wx.StaticBox(self, label = '文件处理', pos = (16, 10), size = (384, 255))
        self.LoadFileButton = wx.Button(Sub_TaskFile, label = '导入文件', pos = (16, 22))
        TaskTitle = wx.StaticText(Sub_TaskFile, label = '当前任务:', pos = (112, 30))
        self.TaskLabel = wx.StaticText(Sub_TaskFile, label = '空闲中', pos = (170, 30))
        self.CorrectCheckBox = wx.CheckBox(Sub_TaskFile, label = '坐标补正', pos = (292, 31))
        self.CorrectCheckBox.SetValue(PaintingfaceConfigs.IsCorrection)
        self.CorrectCheckBox.Disable()
        self.ProcessInfo = wx.TextCtrl(Sub_TaskFile, pos = (17, 66), size = (349, 170), style = wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_NO_VSCROLL)

        self.Sub_Painting = wx.StaticBox(self, label = '差分表情导入', pos = (16, 273), size = (384, 255))
        self.LoadPaintingButton = wx.Button(self.Sub_Painting, label = '导入主立绘', pos = (16, 22), size = (109, 30))
        self.LoadFaceFileButton = wx.Button(self.Sub_Painting, label = '导入差分 - 文件', pos = (137, 22), size = (109, 30))
        self.LoadFace2DButton = wx.Button(self.Sub_Painting, label = '导入差分 - 图片', pos = (258, 22), size = (109, 30))
        self.InfoNotebook = wx.Notebook(self.Sub_Painting, pos = (13, 66), size = (357, 174))
        self.InfoNotebook.SetBackgroundColour('#FFFFFF')
        self.FaceProcessInfo = wx.TextCtrl(self.InfoNotebook, style = wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_NO_VSCROLL)
        self.FaceListBox = wx.ListBox(self.InfoNotebook, style = wx.LB_SINGLE | wx.LB_HSCROLL | wx.LB_OWNERDRAW)
        self.InfoNotebook.AddPage(self.FaceProcessInfo, '处理日志')
        self.InfoNotebook.AddPage(self.FaceListBox, '差分列表')
        self.LoadFace2DButton.Disable()
        self.LoadFaceFileButton.Disable()
        self.Sub_Painting.Disable()

        self.PreviewBook = wx.Notebook(self, pos = (416, 10), size = (872, 570))
        self.PreviewPanel = wx.Panel(self.PreviewBook)
        self.PreviewPanel.SetBackgroundColour('#FFFFFF')
        self.PreviewBook.AddPage(self.PreviewPanel, 'Preview')
        self.PreviewImage = InitImgPre
        self.PreviewPanel.Refresh()
        self.SaveButton = wx.Button(self, label = '保存', pos = (15, 544), size = (186, 36))
        self.SaveButton.Disable()
        self.OpenFolderButton = wx.Button(self, label = '打开文件夹', pos = (215, 544), size = (186, 36))

        self.PreviewPanel.Bind(wx.EVT_ERASE_BACKGROUND, self.DoNothing)
        self.PreviewPanel.Bind(wx.EVT_PAINT, self.RefreshPreview)
        self.LoadFileButton.Bind(wx.EVT_BUTTON, self.LoadFile)
        self.CorrectCheckBox.Bind(wx.EVT_CHECKBOX, self.ApplyCorrection)
        self.LoadPaintingButton.Bind(wx.EVT_BUTTON, self.LoadPainting)
        self.LoadFaceFileButton.Bind(wx.EVT_BUTTON, self.LoadPaintingface_File)
        self.LoadFace2DButton.Bind(wx.EVT_BUTTON, self.LoadPaintingface_2D)
        self.FaceListBox.Bind(wx.EVT_LISTBOX, self.SwitchPreview)
        self.SaveButton.Bind(wx.EVT_BUTTON, self.SaveTo)
        self.OpenFolderButton.Bind(wx.EVT_BUTTON, self.OpenFolder)
    def LoadFile(self, event):
        fileDia = wx.FileDialog(self, message = '导入文件', defaultDir = PaintingfaceConfigs.filesPath)
        if fileDia.ShowModal() == wx.ID_OK:
            self.TaskLabel.SetLabel(fileDia.GetFilename())
            filePath = fileDia.GetPath()
            PaintingfaceConfigs.Update(pf1 = os.path.split(filePath)[0])
            self.InfoNotebook.SetSelection(0)
            return self.Paintingface(filePath)
    def Paintingface(self, ABPath):
        self.CorrectCheckBox.SetValue(PaintingfaceConfigs.IsCorrection)
        self.CorrectCheckBox.Disable()
        self.LoadFace2DButton.Disable()
        self.LoadFaceFileButton.Disable()
        self.FaceProcessInfo.Clear()
        self.FaceListBox.Clear()
        self.InfoNotebook.SetSelection(0)
        self.Sub_Painting.Disable()
        self.SaveButton.Disable()
        self.PreviewImage = InitImgPre
        self.PreviewPanel.Refresh()
        RootPath = './cache/paintigface'
        self.ABBasename = os.path.basename(ABPath)
        self.TextAssetPath = f'{RootPath}/TextAsset'
        self.Texture2DPath = f'{RootPath}/Texture2D'
        if os.path.exists(self.TextAssetPath):
            for cacheFolder in os.listdir(self.TextAssetPath):
                rmtree(f'{self.TextAssetPath}/{cacheFolder}')
        if os.path.exists(self.Texture2DPath):
            for cacheFolder in os.listdir(self.Texture2DPath):
                rmtree(f'{self.Texture2DPath}/{cacheFolder}')
        if not os.path.exists(RootPath): os.mkdir(RootPath)
        if not os.path.exists(self.TextAssetPath): os.mkdir(self.TextAssetPath)
        if not os.path.exists(self.Texture2DPath): os.mkdir(self.Texture2DPath)
        self.cacheTextAssetPath = f'{self.TextAssetPath}/{self.ABBasename}'
        os.mkdir(self.cacheTextAssetPath)
        BaseClassID = ExtractAssetBundle(ABPath, self.cacheTextAssetPath, self.ProcessInfo, 'TextAsset')
        if BaseClassID == -1:
            return -1
        self.ProcessInfo.AppendText('Building RectTransform Object...\n')
        self.RectList = []
        self.FaceList = []
        with open(f'{self.cacheTextAssetPath}/{BaseClassID}.txt', 'r') as BaseData:
            for dataLines in BaseData.readlines():
                if 'm_PathID' in dataLines:
                    ChildrenPathID = dataLines.split(' ')[1]
                    with open(f'{self.cacheTextAssetPath}/{ChildrenPathID}.txt', 'r') as ChildrenData:
                        if 'RectTransform' in ChildrenData.readlines()[0]:
                            MainRectPathID = ChildrenPathID
                            break
        MainRect = RectTransform(self.cacheTextAssetPath, MainRectPathID)
        MainRect.Continue()
        MainRect.SetFatherRectObject(None)
        MainRect.CalculateRectSize()
        MainRect.LocalScale = [Decimal('1'), Decimal('1'), Decimal('1')]
        self.RectList.append(MainRect)
        for FacePathID in MainRect.ChildrenPathID:
            FaceRect = RectTransform(self.cacheTextAssetPath, FacePathID)
            if FaceRect.name == 'face':
                FaceRect.Continue()
                break
        else:
            self.ProcessInfo.AppendText('\nERROR: Useless Unity web file.\n')
            return -1
        self.RectList.append(FaceRect)
        FaceRect.SetFatherRectObject(MainRect)
        FaceRect.CalculateRectSize()
        self.ProcessInfo.AppendText('Calculating coordinates...\n')
        self.FacePastePoint = (
            round(Decimal((FaceRect.AnchorMax[0] - FaceRect.AnchorMin[0]) * MainRect.Size[0] * FaceRect.Pivot[0] + FaceRect.AnchorMin[0] * MainRect.Size[0] + FaceRect.AnchoredPosition[0] - FaceRect.Size[0] * FaceRect.Pivot[0] * FaceRect.LocalScale[0])) + 1,
            round(Decimal((FaceRect.AnchorMax[1] - FaceRect.AnchorMin[1]) * MainRect.Size[1] * FaceRect.Pivot[1] + FaceRect.AnchorMin[1] * MainRect.Size[1] + FaceRect.AnchoredPosition[1] - FaceRect.Size[1] * FaceRect.Pivot[1] * FaceRect.LocalScale[1])) + 1
        )
        self.ExactPastePoint = (self.FacePastePoint[0] - (not PaintingfaceConfigs.IsCorrection), self.FacePastePoint[1] - (not PaintingfaceConfigs.IsCorrection))
        self.CheckList = [False for n in range(0, len(self.RectList))]
        self.PaintingRawSize = tuple(MainRect.RawSize)
        self.FileName = f'{PaintingConfigs.paintingPath}\{self.ABBasename}_exp.png'
        self.WildCard_Painting = f'Required Files ({PaintingConfigs.wildCard})|{PaintingConfigs.wildCard}|All Paintings (*.png)|*.png'.replace(r'{name}', self.ABBasename)
        self.WildCard_Face2D = f'Required Files ({PaintingfaceConfigs.wildCard2D})|{PaintingfaceConfigs.wildCard2D}|All Paintingface (*.png)|*.png'.replace(r'{name}', self.ABBasename)
        self.WildCard_FaceFile = f'Required Files ({PaintingfaceConfigs.wildCardFile})|{PaintingfaceConfigs.wildCardFile}|All Files (*.*)|*.*'.replace(r'{name}', '_'.join(self.ABBasename.split('_', 2)[:2]))
        self.ProcessInfo.AppendText('\nDone! Please load painting & paintingface.\n')
        self.Sub_Painting.Enable()
    def LoadPainting(self, event):
        paintingDia = wx.FileDialog(self, message = '导入立绘', defaultDir = PaintingConfigs.paintingPath, wildcard = self.WildCard_Painting)
        if paintingDia.ShowModal() == wx.ID_OK:
            PaintingPath = paintingDia.GetPath()
            Painting = Image.open(PaintingPath).transpose(Image.FLIP_TOP_BOTTOM)
            self.MainPainting = Image.new('RGBA', self.PaintingRawSize, (0, 0, 0, 0))
            self.MainPainting.paste(Painting, (0, 0))
            PaintingConfigs.Update(p2 = os.path.split(PaintingPath)[0])
            self.FileName = f'{PaintingConfigs.paintingPath}\{self.ABBasename}_exp.png'
            self.CheckList[0] = True
            self.CorrectCheckBox.Enable()
            self.LoadFace2DButton.Enable()
            self.LoadFaceFileButton.Enable()
            return self.PasteFace()
    def LoadPaintingface_2D(self, event):
        Face2DDia = wx.FileDialog(self, message = '导入差分表情', defaultDir = PaintingfaceConfigs.face2DPath, wildcard = self.WildCard_Face2D)
        if Face2DDia.ShowModal() == wx.ID_OK:
            self.FaceList = []
            self.FaceNameList = []
            FacePath = Face2DDia.GetPath()
            Face = Image.open(FacePath).transpose(Image.FLIP_TOP_BOTTOM)
            PaintingfaceConfigs.Update(pf2 = os.path.split(FacePath)[0])
            self.FaceList.append(Face)
            self.FaceNameList.append(Face2DDia.GetFilename())
            self.FaceProcessInfo.Clear()
            self.CheckList[1] = True
            return self.PasteFace()
    def LoadPaintingface_File(self, event):
        FaceFileDia = wx.FileDialog(self, message = '导入差分表情文件', defaultDir = PaintingfaceConfigs.faceFilePath, wildcard = self.WildCard_FaceFile)
        if FaceFileDia.ShowModal() == wx.ID_OK:
            filePath = FaceFileDia.GetPath()
            PaintingfaceConfigs.Update(pf3 = os.path.split(filePath)[0])
            self.InfoNotebook.SetSelection(0)
            return self.PaintingfaceTexture2D(filePath)
    def PaintingfaceTexture2D(self, ABPath):
        self.FaceProcessInfo.Clear()
        if os.path.exists(self.Texture2DPath):
            for cacheFolder in os.listdir(self.Texture2DPath):
                rmtree(f'{self.Texture2DPath}/{cacheFolder}')
        self.cacheTexture2DPath = f'{self.Texture2DPath}/{self.ABBasename}'
        os.mkdir(self.cacheTexture2DPath)
        resSFilePath = ExtractAssetBundle(ABPath, self.cacheTexture2DPath, self.FaceProcessInfo, 'Texture2D')
        if resSFilePath == -1:
            resSFilePath = ExtractAssetBundle(ABPath, self.cacheTexture2DPath, self.FaceProcessInfo, 'TextAsset', 1)
            if resSFilePath != 1:
                self.FaceProcessInfo.AppendText('\nERROR: Invalid paintingface AssetBundle.\n')
                return -1
        self.FaceList = []
        self.FaceNameList = []
        SpriteOffsetList = []
        SpriteSizeList = []
        TexturePathIDList = []
        TexNameList = []
        TexRectOffset = [0, 0]
        TexRectSize = [0, 0]
        with open(f'{self.cacheTexture2DPath}/1.txt', 'r') as ABAssetEnum:
            ABInfo = ABAssetEnum.readlines()
            for dataLines in ABInfo:
                if 'm_PathID' in dataLines:
                    if 'data' in ABInfo[ABInfo.index(dataLines) - 2]:
                        AssetPathID = dataLines.split(' ')[1]
                        with open(f'{self.cacheTexture2DPath}/{AssetPathID}.txt', 'r') as Asset:
                            AssetComponent = Asset.readlines()
                            if 'Sprite' in AssetComponent[0]:
                                for SpriteDataLines in AssetComponent:
                                    if 'm_Name' in SpriteDataLines:
                                        self.FaceNameList.append(SpriteDataLines.split('"')[1])
                                    elif 'm_Rect' in SpriteDataLines:
                                        TextureRectInfo = AssetComponent[AssetComponent.index(SpriteDataLines) + 1 : AssetComponent.index(SpriteDataLines) + 5]
                                        for TexRectLines in TextureRectInfo:
                                            if 'width' in TexRectLines:
                                                TexRectSize[0] = round(Decimal(TexRectLines.split(' ')[1]))
                                            elif 'height' in TexRectLines:
                                                TexRectSize[1] = round(Decimal(TexRectLines.split(' ')[1]))
                                    elif 'texture  (PPtr<Texture2D>)' in SpriteDataLines:
                                        TextureInfo = AssetComponent[AssetComponent.index(SpriteDataLines) + 1 : AssetComponent.index(SpriteDataLines) + 3]
                                        for TexInfo in TextureInfo:
                                            if 'm_PathID' in TexInfo:
                                                TexturePathID = TexInfo.split(' ')[1]
                                                TexturePathIDList.append(TexturePathID)
                                                with open(f'{self.cacheTexture2DPath}/{TexturePathID}.txt', 'r') as TexData:
                                                    for TexDataLines in TexData.readlines():
                                                        if 'm_Name' in TexDataLines:
                                                            TexNameList.append(TexDataLines.split('"')[1])
                                                            break
                                    elif 'textureRect  (Rectf)' in SpriteDataLines:
                                        SpriteRectInfo = AssetComponent[AssetComponent.index(SpriteDataLines) + 1 : AssetComponent.index(SpriteDataLines) + 5]
                                        for SpriteRectLines in SpriteRectInfo:
                                            if 'x' in SpriteRectLines:
                                                TexRectOffset[0] = round(Decimal(SpriteRectLines.split(' ')[1]))
                                            elif 'y' in SpriteRectLines:
                                                TexRectOffset[1] = round(Decimal(SpriteRectLines.split(' ')[1]))
                                SpriteOffsetList.append(tuple(TexRectOffset))
                                SpriteSizeList.append(tuple(TexRectSize))
        FaceNamePathIDDict = dict(zip(self.FaceNameList, TexturePathIDList))
        SpriteNameOffsetDict = dict(zip(self.FaceNameList, SpriteOffsetList))
        SpriteNameSizeDict = dict(zip(self.FaceNameList, SpriteSizeList))
        try:
            SortList = [int(m) for m in self.FaceNameList]
        except ValueError:
            self.FaceProcessInfo.AppendText('\nERROR: Invalid Unity web file.\n')
            return -1
        TexturePathIDSet = set(TexturePathIDList)
        IsCutting = True if len(TexturePathIDSet) != len(self.FaceNameList) else False
        SortList.sort()
        self.FaceNameList = [str(n) for n in SortList]
        self.FaceProcessInfo.AppendText('Building Paintingface images...\n')
        if not IsCutting:
            if resSFilePath != 1:
                with open(resSFilePath, 'rb') as resSData:
                    for FaceName in self.FaceNameList:
                        FaceImage = self.Texture2DFromResS(FaceNamePathIDDict.get(FaceName), resSData)
                        self.FaceList.append(FaceImage)
            else:
                for FaceName in self.FaceNameList:
                    FaceImage = self.Texture2DFromString(FaceNamePathIDDict.get(FaceName))
                    self.FaceList.append(FaceImage)
        else:
            if resSFilePath != 1:
                with open(resSFilePath, 'rb') as resSData:
                    TextureList = []
                    for TexPathID in TexturePathIDSet:
                        TextureList.append(self.Texture2DFromResS(TexPathID, resSData))
                    TexPathIDDict = dict(zip(TexturePathIDSet, TextureList))
            else:
                TextureList = []
                for TexPathID in TexturePathIDSet:
                    TextureList.append(self.Texture2DFromString(TexPathID))
                TexPathIDDict = dict(zip(TexturePathIDSet, TextureList))
            for FaceName in self.FaceNameList:
                offset = SpriteNameOffsetDict.get(FaceName)
                size = SpriteNameSizeDict.get(FaceName)
                FaceImage = TexPathIDDict.get(FaceNamePathIDDict.get(FaceName)).crop(offset + (offset[0] + size[0], offset[1] + size[1]))
                self.FaceList.append(FaceImage)
        self.CheckList[1] = True
        self.FaceProcessInfo.AppendText('\nDone!\n')
        return self.PasteFace()
    def Texture2DFromResS(self, TexturePathID, resSData):
        StreamOffset = 0
        StreamSize = 0
        FaceSize = [0, 0]
        with open(f'{self.cacheTexture2DPath}/{TexturePathID}.txt', 'r') as TextureData:
            TextureDataList = TextureData.readlines()
            for dataLines in TextureDataList:
                if 'm_Width' in dataLines:
                    FaceSize[0] = int(dataLines.split(' ')[1])
                elif 'm_Height' in dataLines:
                    FaceSize[1] = int(dataLines.split(' ')[1])
                elif 'm_StreamData' in dataLines:
                    StreamDataList = TextureDataList[TextureDataList.index(dataLines) + 1 : TextureDataList.index(dataLines) + 3]
                    for StreamData in StreamDataList:
                        if 'offset' in StreamData:
                            StreamOffset = int(StreamData.split(' ')[1])
                        elif 'size' in StreamData:
                            StreamSize = int(StreamData.split(' ')[1])
        resSData.seek(StreamOffset)
        ImageData = resSData.read(StreamSize)
        try:
            FaceImage = Image.frombuffer('RGBA', tuple(FaceSize), ImageData, 'raw', 'RGBA', 0, 1)
        except ValueError:
            ImageData = tex2img.decompress_etc(ImageData, FaceSize[0], FaceSize[1], 3)
            FaceImage = Image.frombuffer('RGBA', tuple(FaceSize), ImageData, 'raw', 'RGBA', 0, 1)
        return FaceImage
    def Texture2DFromString(self, TexturePathID):
        dataList = []
        FaceSize = [0, 0]
        with open(f'{self.cacheTexture2DPath}/{TexturePathID}.txt', 'r') as TextureData:
            TextureDataList = TextureData.readlines()
            for dataLines in TextureDataList:
                if 'm_Width' in dataLines:
                    FaceSize[0] = int(dataLines.split(' ')[1])
                elif 'm_Height' in dataLines:
                    FaceSize[1] = int(dataLines.split(' ')[1])
                elif 'data' in dataLines:
                    imgData = dataLines.split(': ')[1].split(' ')
                    imgIntData = [int(x) for x in imgData]
                    dataList.extend(imgIntData)
        databytes = bytes(dataList)
        try:
            FaceImage = Image.frombytes('RGBA', tuple(FaceSize), databytes, 'raw')
        except ValueError:
            databytes = tex2img.decompress_etc(databytes, FaceSize[0], FaceSize[1], 3)
            FaceImage = Image.frombytes('RGBA', tuple(FaceSize), databytes, 'raw')
        return FaceImage
    def PasteFace(self):
        self.PaintingWithFaceList = []
        for face in self.FaceList:
            Painting = self.MainPainting.copy()
            FaceBlank = Image.new('RGBA', Painting.size, (0, 0, 0, 0))
            FaceBlank.paste(face, self.ExactPastePoint)
            Painting = Image.alpha_composite(Painting, FaceBlank)
            self.PaintingWithFaceList.append(Painting.transpose(Image.FLIP_TOP_BOTTOM))
        if not self.PaintingWithFaceList:
            self.PaintingWithFace = self.MainPainting.copy().transpose(Image.FLIP_TOP_BOTTOM)
        else:
            self.FaceNamePaintingDict = dict(zip(self.FaceNameList, self.PaintingWithFaceList))
            self.PaintingWithFace = self.PaintingWithFaceList[0]
            self.FaceListBox.SetItems(self.FaceNameList)
            self.FaceListBox.SetSelection(0)
            self.InfoNotebook.SetSelection(1)
        if len(set(self.CheckList)) == 1 and set(self.CheckList) == {True}:
            self.SaveButton.Enable()
        self.PreviewImage = ReleasePreview(self.PaintingWithFace)
        self.PreviewPanel.Refresh()
        return 0
    def ApplyCorrection(self, event):
        if self.CorrectCheckBox.GetValue():
            self.ExactPastePoint = self.FacePastePoint
        elif not self.CorrectCheckBox.GetValue():
            self.ExactPastePoint = (self.FacePastePoint[0] - 1, self.FacePastePoint[1] - 1)
        return self.PasteFace()
    def SwitchPreview(self, event):
        self.PaintingWithFace = self.FaceNamePaintingDict.get(self.FaceListBox.GetStringSelection())
        self.PreviewImage = ReleasePreview(self.PaintingWithFace)
        self.PreviewPanel.Refresh()
        return 0
    def SaveTo(self, event):
        self.SwitchPreview(None)
        self.PaintingWithFace.save(self.FileName)
        return 0
    def OpenFolder(self, event):
        try:
            if not os.path.exists(self.FileName):
                os.popen(f'explorer {PaintingConfigs.paintingPath}')
            else:
                os.popen(f'explorer /select,"{self.FileName}"')
        except:
            os.popen(f'explorer {PaintingConfigs.paintingPath}')
        return 0
    def RefreshPreview(self, event):
        buffer = wx.BufferedPaintDC(self.PreviewPanel)
        buffer.Clear()
        try:
            buffer.DrawBitmap(self.PreviewImage, x = 0, y = 0)
        except:
            pass
        return 0
    def DoNothing(self, event):
        return 0
class WorkFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent = None, title = '操作面板', size = (1359, 690), style = wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX)
        self.Centre()
        FramePanel = wx.Panel(self)
        PanelBook = wx.Notebook(FramePanel, pos = (17, 10), size = (1311, 625))
        PanelBook.SetBackgroundColour('#F0F0F0')
        PaintingPanel = PaintingFrame(PanelBook)
        PaintingfacePanel = PaintingfaceFrame(PanelBook)
        PanelBook.AddPage(PaintingPanel, '立绘合并')
        PanelBook.AddPage(PaintingfacePanel, '差分接头')
        self.Bind(wx.EVT_CLOSE, self.OnClose)
    def OnClose(self, event):
        self.Destroy()
        for cacheFolder in os.listdir('./cache'):
            rmtree(f'./cache/{cacheFolder}', ignore_errors = True)
        configFile.update(PaintingConfigs.FileForm())
        configFile.update(PaintingfaceConfigs.FileForm())
        with open('ALPAConfigs.yml', 'w', encoding = 'utf-8') as yamlFile:
            yaml.safe_dump(configFile, yamlFile, allow_unicode = True, sort_keys = False)
        return 0

InitImg = Image.new('RGBA', (864, 540), (255, 255, 255, 255))
TextFont = ImageFont.truetype('arialbd', 54)
DrawImage = ImageDraw.Draw(InitImg)
DrawImage.text((318, 193), ' Preview\n     not\navailable', fill = (116, 116, 116), font = TextFont)
InitImgData = InitImg.convert('RGB').tobytes()
with open('ALPAConfigs.yml', encoding = 'utf-8') as yamlFile:
    configFile = yaml.safe_load(yamlFile)
PaintingConfigs = PaintingSetting(configFile.get('painting'))
PaintingfaceConfigs = PaintingfaceSetting(configFile.get('paintingface'))
MainApp = wx.App()
InitImgPre = wx.Bitmap(img = wx.Image(width = 864, height = 540, data = InitImgData))
CtrlFrame = WorkFrame()
CtrlFrame.Show()
MainApp.MainLoop()