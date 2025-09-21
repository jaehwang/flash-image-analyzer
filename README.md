# Gang Image 분석 도구

임베디드 시스템에서 사용되는 gang image를 분석하고 검증하는 CLI 도구입니다.

## Gang Image란 무엇인가?

### 개념

Gang image는 여러 개의 펌웨어 구성 요소를 하나의 바이너리 파일로 묶어서 플래시 메모리에 프로그래밍하는 형식입니다. 주로 다음과 같은 임베디드 시스템에서 사용됩니다:

- **라우터 펌웨어**: 공유기, 스위치 등 네트워크 장비
- **IoT 디바이스**: 스마트 홈 기기, 센서 노드
- **모바일 디바이스**: 스마트폰, 태블릿
- **산업용 장비**: 의료기기, 자동차 ECU, 산업 제어기

### 장점

1. **제조 공정 단순화**: 하나의 파일로 전체 시스템 이미지를 한 번에 프로그래밍
2. **버전 관리 용이성**: 모든 구성 요소의 호환성을 보장하는 단일 이미지
3. **품질 관리**: 검증된 구성 요소들의 조합으로 안정성 확보
4. **배포 효율성**: 펌웨어 업데이트 시 단일 파일로 배포

### 전형적인 Gang Image 구조

```
┌──────────────────────┐ 0x00000000
│  Primary Bootloader  │ (1차 부트로더 - 하드웨어 초기화)
├──────────────────────┤ 0x00040000
│  Secondary Bootloader│ (2차 부트로더 - U-Boot 등)
├──────────────────────┤ 0x00100000
│  Environment         │ (부트로더 환경 변수)
├──────────────────────┤ 0x00120000
│  Device Tree         │ (하드웨어 정보)
├──────────────────────┤ 0x00140000
│  Kernel Image        │ (Linux 커널)
├──────────────────────┤ 0x00800000
│  Root FileSystem     │ (루트 파일시스템)
├──────────────────────┤ 0x04000000
│  User Data           │ (사용자 데이터)
├──────────────────────┤ 0x07000000
│  Configuration       │ (설정 데이터)
├──────────────────────┤ 0x07E00000
│  Recovery/Backup     │ (복구용 이미지)
└──────────────────────┘ 0x08000000
```

### 부팅 과정

1. **Boot ROM**: SoC 내장 ROM에서 첫 번째 부트 코드 실행
2. **Primary Bootloader**: 기본 하드웨어 초기화 (DDR, 클록 설정)
3. **Secondary Bootloader**: 고급 부트로더 (네트워크, USB 지원)
4. **Kernel Loading**: Linux 커널을 메모리에 로드하여 실행
5. **File System Mount**: 루트 파일시스템 마운트 및 사용자 공간 실행

## 칩셋별 차이점

임베디드 시스템에서 gang image의 구조와 형식은 사용하는 칩셋에 따라 크게 달라집니다. 각 칩셋 제조사는 자체적인 부팅 방식과 메모리 레이아웃을 가지고 있어 서로 다른 도구와 분석 방법이 필요합니다.

### 주요 칩셋별 특성

#### Qualcomm 플랫폼
```
특징:
- MBN (Multi-Boot Image) 형식 사용
- TrustZone 보안 아키텍처
- RPM (Resource Power Manager) 독립 실행
- QFIL 도구로 플래시 프로그래밍

메모리 레이아웃:
0x40000000 ~ 0x4FFFFFFF: SBL (Secondary Boot Loader)
0x86000000 ~ 0x87FFFFFF: TZ (TrustZone)
0x60000000 ~ 0x6FFFFFFF: RPM (Resource Power Manager)
0x8F600000 ~ 0x8F6FFFFF: APPSBL (Application SBL)
0x90000000 ~           : Rootfs/User Data

지원 파일시스템: UBIFS, ext4, SquashFS

테스트 샘플 구조:
- SBL (0x40000000): 4KB 부트로더
- APPSBL (0x8F600000): 2KB 애플리케이션 부트로더
- Rootfs (0x90000000): 1MB+
```

#### Broadcom 플랫폼
```
특징:
- CFE (Common Firmware Environment) 부트로더
- NVRAM 영역에 설정 저장
- 주로 네트워크 장비에 사용
- 간단한 TRX 헤더 형식

메모리 레이아웃:
0x00000000: CFE 부트로더
0x00010000: NVRAM (설정 데이터)
0x00020000: Linux 커널
0x00200000: SquashFS 루트 파일시스템
0x00800000: JFFS2 (설정용 쓰기 가능 영역)

지원 파일시스템: SquashFS, JFFS2, CramFS
```

#### MediaTek 플랫폼
```
특징:
- Preloader + U-Boot 이중 부트로더
- Android 스타일 파티션 구조
- SP Flash Tool로 프로그래밍
- 스마트폰, 태블릿에 주로 사용

메모리 레이아웃:
0x00000000: Preloader
0x00040000: U-Boot
0x00080000: Boot (kernel + ramdisk)
0x00800000: Recovery
0x01000000: System (Android 루트)
0x04000000: Userdata

지원 파일시스템: ext4, F2FS, UBIFS
```

#### Marvell 플랫폼
```
특징:
- U-Boot 기반 부트로더
- 네트워크 프로세서에 특화
- 다중 CPU 코어 지원
- 스위치/라우터에 주로 사용

메모리 레이아웃:
0x00000000: U-Boot
0x00100000: 환경 변수
0x00200000: Linux 커널
0x00800000: 루트 파일시스템

지원 파일시스템: ext2/3/4, SquashFS
```

### 분석 도구 확장 계획

현재 Qualcomm 플랫폼을 시작으로, 다음 순서로 지원을 확장할 예정입니다:

1. **✅ Qualcomm** (현재 지원) - MBN 형식, TrustZone 구조
2. **📋 Broadcom** - CFE, TRX 헤더 형식
3. **📋 MediaTek** - Preloader, Android 파티션
4. **📋 Marvell** - U-Boot, 네트워크 프로세서
5. **📋 기타 플랫폼** - 사용자 요구에 따라 추가

## Qualcomm Gang Image 분석 도구

### 개요

Qualcomm 플랫폼용 gang image를 분석하는 CLI 도구입니다. MBN (Multi-Boot Image) 형식을 지원하며, 파티션 구조 분석, 파일시스템 검사, 무결성 검증 기능을 제공합니다.

### 주요 기능

#### 핵심 분석 기능

- **MBN 헤더 파싱**: Qualcomm의 Multi-Boot Image 형식 분석
- **ELF 형식 지원**: ELF 기반 gang image 처리
- **자동 파티션 감지**: 부트로더, 커널, 파일시스템 자동 식별
- **메모리 레이아웃 검증**: 오버랩 및 정렬 문제 검사
- **무결성 검증**: CRC32 체크섬 및 크기 검증

#### 파일시스템 분석

임베디드 시스템에서 사용되는 다양한 파일시스템을 분석합니다:

| 파일시스템 | 설명 | 분석 기능 |
|-----------|------|----------|
| **ext2/3/4** | 표준 Linux 파일시스템 | 슈퍼블록 완전 분석 |
| **SquashFS** | 압축 읽기 전용 파일시스템 | 크기 및 압축 정보 |
| **UBIFS** | NAND 플래시 최적화 파일시스템 | 기본 구조 분석 |
| **JFFS2** | 저널링 플래시 파일시스템 | 노드 구조 스캔 |
| **YAFFS2** | NAND 플래시 전용 파일시스템 | 패턴 기반 탐지 |

#### 파티션 타입 감지

다음 기준으로 파티션 타입을 자동 식별합니다:
- **로드 주소**: Qualcomm 메모리 맵 기반
- **내용 분석**: 매직 넘버, 시그니처 확인
- **크기 패턴**: 일반적인 레이아웃 패턴

### 설치 방법

#### 필요 조건

- Python 3.8.1 이상
- uv (권장) 또는 pip

#### uv를 사용한 설치 (권장)

```bash
# uv 설치 (미설치 시)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 프로젝트 의존성 설치
uv sync
uv pip install -e ".[dev]"
# 또는
make install-dev

# 개발 모드로 설치
uv pip install -e .
# 또는
make install
```

#### 전통적인 pip 설치

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 개발 모드로 설치
pip install -e .
```

### 사용 방법

#### uv를 사용한 실행 (권장)

```bash
# 도움말 확인
uv run python -m gangimg.cli --help

# gang image 분석
uv run python -m gangimg.cli firmware.bin

# 상세 정보와 함께 분석
uv run python -m gangimg.cli -v firmware.bin
```

#### 설치 후 실행

```bash
# 패키지 설치 후
gangimg --help
gangimg firmware.bin
gangimg -v firmware.bin
```

#### 고급 옵션

```bash
# 파일시스템 분석 제외 (빠른 처리)
uv run python -m gangimg.cli --no-fs-analysis firmware.bin

# 파일시스템이 있는 파티션만 표시
uv run python -m gangimg.cli --fs-only firmware.bin

# 특정 파티션 추출
uv run python -m gangimg.cli --extract system_0:extracted_system.bin firmware.bin

# JSON 출력 형식
uv run python -m gangimg.cli --output-format json firmware.bin

# 플랫폼 지정
uv run python -m gangimg.cli --platform qualcomm firmware.bin
```

#### 테스트용 샘플 생성 및 분석

테스트를 위한 Qualcomm 명세 준수 gang image를 생성하고 분석할 수 있습니다:

```bash
# 1. Qualcomm gang image 샘플 생성 (MBN 파티션 구조, SquashFS rootfs 포함)
uv run python scripts/create_simple_sample.py

# 2. 생성된 gang image 분석
uv run python -m gangimg.cli samples/simple_gang.img

# 또는 Makefile로 분석 (샘플 생성 후)
make example
```

생성되는 gang image는 다음과 같은 구조를 가집니다:
- **SBL 파티션**: Secondary Boot Loader (4KB, 0x40000000)
- **APPSBL 파티션**: Application SBL (2KB, 0x8F600000)
- **Rootfs 파티션**: SquashFS 형식 (1MB+, README.md 파일 포함)

이 스크립트는 Qualcomm 명세에 맞는 **MBN (Multi-Boot Image) 형식**을 사용하여:
- 각 파티션마다 40바이트 MBN 헤더 구조 생성
- Qualcomm 메모리 맵에 따른 로드 주소 할당
- SquashFS 압축 파일시스템으로 rootfs 구현
- 분석 도구가 인식할 수 있는 완전한 gang image 생성

### 출력 예시

#### 기본 파티션 정보
```
Found 3 partitions:
------------------------------------------------------------------------------------------------------------------------
Name            Type       Offset       Size         Load Addr    FS Type    FS Size      Used
------------------------------------------------------------------------------------------------------------------------
sbl_0           sbl        0x00000000   4.0KB        0x40000000   N/A        N/A        N/A
appsbl_1        appsbl     0x00002000   2.0KB        0x8f600000   N/A        N/A        N/A
unknown_2       unknown    0x00003000   1.0MB        0x90000000   squashfs   1.0KB      1.0KB
------------------------------------------------------------------------------------------------------------------------
Total partition size: 1.0MB
Total filesystem used: 1.0KB
File size: 1.0MB
Unused space: 5.9KB
```

#### 파일시스템 상세 정보
```
Filesystem Details:
----------------------------------------------------------------------------------------------------
Partition       FS Type    Total        Used         Free         Usage%   Block Size
----------------------------------------------------------------------------------------------------
unknown_2       squashfs   1.0KB        1.0KB        0B           100.0%   128.0KB
----------------------------------------------------------------------------------------------------
```

#### 검증 결과
```
Overlap Analysis:
----------------------------------------
✅ 오버랩 없음

Partition Validation:
----------------------------------------
✅ 모든 파티션 검증 성공
```

### 출력 해석 가이드

#### 파티션 정보 필드 설명

- **Name**: 자동 생성된 파티션 식별자
- **Type**: 감지된 파티션 타입 (sbl, tz, rpm, boot 등)
- **Offset**: gang image 내에서의 시작 위치
- **Size**: 물리적 파티션 크기
- **Load Addr**: 부팅 시 로드되는 메모리 주소
- **FS Type**: 감지된 파일시스템 타입 (해당하는 경우)
- **FS Size**: 논리적 파일시스템 크기
- **Used**: 파일시스템에서 실제 사용 중인 공간

#### 크기 구분

##### 파티션 크기 vs 파일시스템 크기
- **파티션 크기**: 플래시 메모리에 할당된 물리적 공간
- **파일시스템 크기**: 파일시스템이 사용 가능한 논리적 공간
- **사용 공간**: 실제 데이터가 저장된 공간

예시:
```
파티션 크기: 64MB     (할당된 플래시 공간)
FS 크기: 58MB        (파일시스템 오버헤드 제외 후 사용 가능 공간)
사용: 45MB           (실제 데이터)
여유: 13MB           (새 데이터를 위한 여유 공간)
```

### 추출된 파티션 마운트

파티션 추출 후 호스트 시스템에서 마운트할 수 있습니다:

#### 파일시스템 파티션

```bash
# 파일시스템 파티션 추출
python gangimg firmware.bin --extract system_0:system.bin

# 파일시스템 타입 확인
file system.bin

# 파티션 마운트
sudo mkdir /mnt/extracted
sudo mount -o loop system.bin /mnt/extracted

# 특정 파일시스템 타입으로 마운트:
sudo mount -t squashfs -o loop system.bin /mnt/extracted
sudo mount -t ext4 -o loop system.bin /mnt/extracted
```

#### 마운트 불가능한 파티션

부트로더 및 펌웨어 파티션은 마운트할 수 없지만 분석 가능합니다:

```bash
# 부트로더 추출
python gangimg firmware.bin --extract sbl_0:bootloader.bin

# 헥스 에디터나 디스어셈블러로 분석
hexdump -C bootloader.bin | head
objdump -D -b binary -m arm bootloader.bin
```

### 문제 해결

#### 일반적인 문제들

##### 파일을 찾을 수 없음
```bash
Error: File firmware.bin not found
```
**해결책**: 파일 경로와 권한을 확인하세요

##### 파티션이 감지되지 않음
```bash
Gang header not found, scanning for individual MBN images...
Found 0 partitions
```
**해결책**:
- 실제로 gang image인지 확인
- `--verbose` 옵션으로 상세 정보 확인
- 파일이 암호화되거나 압축되어 있는지 확인

##### 파일시스템 분석 오류
```bash
Warning: Error analyzing filesystem at offset 0x00800000: ...
```
**해결책**:
- `--no-fs-analysis` 옵션으로 파일시스템 감지 건너뛰기
- 파일시스템이 손상되었거나 비표준 형식일 수 있음

#### 성능 고려사항

- **대용량 파일**: 1GB 이상 파일은 `--no-fs-analysis` 사용
- **네트워크 저장소**: 분석 전 로컬로 파일 복사
- **메모리 사용량**: 도구는 최소한의 메모리 사용, 청크 단위 처리

### 향후 계획

#### 기능 확장
- **압축 파일 지원**: gzip, lzma 압축된 gang image
- **암호화 감지**: 암호화된 파티션 식별
- **GUI 인터페이스**: 그래픽 사용자 인터페이스 추가
- **배치 처리**: 여러 파일 동시 분석

#### 플랫폼 확장
다음 플랫폼 지원을 위한 개발이 진행 중입니다:
- **Broadcom**: CFE 부트로더, TRX 헤더 지원
- **MediaTek**: Preloader, Android 파티션 구조
- **Marvell**: 네트워크 프로세서 특화 기능

### 기여 방법

#### 새로운 파일시스템 지원 추가

새로운 파일시스템 지원을 추가하려면:

1. `_analyze_filesystem()`에 감지 로직 추가
2. `_analyze_xxx_filesystem()`에 파서 구현
3. enum에 파일시스템 타입 추가
4. 문서 업데이트

#### 플랫폼 확장

다른 플랫폼 지원을 위해 도구를 확장할 수 있습니다:
- Broadcom CFE 형식
- MediaTek 형식
- 사용자 정의 벤더 형식

### 참고 자료

- [Qualcomm Boot Flow 문서](https://developer.qualcomm.com)
- [MTD (Memory Technology Device) 서브시스템](https://www.linux-mtd.infradead.org/)
- [U-Boot 문서](https://docs.u-boot.org/)
- [SquashFS 형식 명세](https://github.com/plougher/squashfs-tools)
