import base64
from io import BytesIO
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from PIL import Image
from typing import List
import argparse


def get_file_content_chrome(driver, uri):
    result: str = driver.execute_async_script(
        """
    var uri = arguments[0];
    var callback = arguments[1];
    var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
    var xhr = new XMLHttpRequest();
    xhr.responseType = 'arraybuffer';
    xhr.onload = function(){ callback(toBase64(xhr.response)) };
    xhr.onerror = function(){ callback(xhr.status) };
    xhr.open('GET', uri);
    xhr.send();
    """,
        uri,
    )
    if type(result) == int:
        raise Exception("Request failed with status %s" % result)
    return base64.b64decode(result)


def merge_images(image_list: List[Image.Image]):
    width = max([image.width for image in image_list])
    height = sum([image.height for image in image_list])
    merged_image = Image.new("RGB", (width, height))
    y = 0
    for image in image_list:
        merged_image.paste(image, (0, y))
        y += image.height
    return merged_image


def is_current_page_exist(driver: uc.Chrome, page_count: int):
    try:
        driver.find_element(By.ID, f"content-p{page_count}")
    except:
        # There's probably a better way than this
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ARROW_LEFT)
        try:
            driver.find_element(By.ID, f"content-p{page_count}")
        except:
            return False
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Use reader link")
    parser.add_argument("url", metavar="URL", type=str, help="Input URL", required=True)
    parser.add_argument("-o", "--Output", help="Output dir")
    parser.parse_args()

    driver = uc.Chrome()
    driver.implicitly_wait(5)
    driver.get(
        "https://michikusacomics.jp/wp-content/uploads/data/27_hutsukoi/01/index.html"
    )

    page_count = 0
    while is_current_page_exist(driver, page_count) is True:
        page = []
        for element in (
            driver.find_element(By.ID, f"content-p{page_count}")
            .find_element(By.CLASS_NAME, "pt-img")
            .find_elements(By.XPATH, ".//div//img")
        ):
            bytes = get_file_content_chrome(driver, element.get_attribute("src"))
            page.append(Image.open(BytesIO(bytes)))
        page = merge_images(page)
        page.save(f"{page_count+1}.png")
