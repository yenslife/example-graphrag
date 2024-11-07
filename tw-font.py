import matplotlib
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager

def tw_font():
    font = 'Microsoft JhengHei' # 如果是 Windows 的電腦才可以用

    for i in sorted(fontManager.get_font_names()):
        if 'Heiti' in i: # Mac 的繁體中文
            font = i
            break
        if 'PingFang' in i:
            font = i
            break

    matplotlib.rc('font', family=font)
    plt.pie(
        [800, 300, 400],
        labels=['交通', '住宿', '餐飲'],
        autopct='%1.1f%%'
    )
    plt.show()

    return font

if __name__ == '__main__':
    tw_font()
