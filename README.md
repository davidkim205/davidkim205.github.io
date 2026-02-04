## 소개
아래 링크에서 Tech Blog를 확인하실 수 있습니다.
https://davidkim205.github.io/

### Markdown to HTML Converter
`converter.py`는 마크다운 문서를 Bulma CSS 기반의 연구 블로그 형식 HTML로 변환하는 코드입니다.
입력 마크다운 파일과 출력 HTML 파일 이름을 모두 지정해야 합니다.

```
python converter.py <input.md> <output.html>
```

**in/out file**: `md` -> `html`


### 추가 & 수정 사항

#### 1. 이미지 폴더 생성

```
static/
├── css/
├── js/
└── images/
    └── 프로젝트명/        # 프로젝트별 폴더 생성
        ├── figure1.png
        ├── figure2.png
        └── ...
```

#### 2. HTML 메타데이터 수정

생성된 HTML 파일에서 다음 항목들을 수정하세요:

- **Author 정보** : 저자 이름 및 프로필 링크
- **Paper/Code/Dataset 링크** : 실제 해당 URL로 변경
- **Footer** : 저자 정보 동일

#### 3. index.html에 프로젝트 추가
`report-container` 안의 `report-box box` class로 프로젝트를 추가합니다.

#### 4. 기울임체 반영
`<em></em>` 으로 직접 설정합니다.