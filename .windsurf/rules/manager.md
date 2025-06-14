---
trigger: manual
---

## 코드수정시 부분코드만 수정하지말고, 전체적인 흐름과 수정 되는 코드 앞과 뒤를 확인해서 최적화하여 코드 수정을 한다.

## Next.js: Route Handler 우선 사용

-   **모든 API 엔드포인트는 Route Handler를 사용하여 구현하세요.**
-   **데이터베이스 작업, 외부 API 호출, 인증 등 복잡한 서버 작업은 반드시 Route Handler를 사용하세요.**
-   **Server Action은 단순 폼 제출 또는 간단한 데이터 처리에만 사용하세요.**

---

## Next.js 라우팅: App Router 사용

-   **프로젝트 내 라우팅은 Pages Router 대신 App Router를 사용하세요.**

---

## 프로젝트 구조: 주요 폴더 구조 예시

-   **프로젝트 구조는 다음과 같이 설정하세요. `src` 폴더는 사용하지 않습니다.**

```

your-nextjs-project/
│
├── app/                      # App Router 라우트 폴더
│ ├── api/                    # API 엔드포인트 관련 폴더
│ ├── dashboard/              # 개별 페이지 폴더 예시 (재사용되지 않는 컴포넌트 포함)
│ └─├── page.tsx              # dashboard 페이지
│   └── DashboardStats.tsx    # 페이지 전용 컴포넌트
├── components/               # 공통 컴포넌트 모음
│ ├── ui                      # ShadCN 공통 UI 컴포넌트
│ │ ├── button.tsx
│ │ ├── input.tsx
│ │ ├── select.tsx
│ │ ├── toast.tsx
│ │ ├── toaster.tsx
│ ├── layout/                 # 레이아웃 관련 공통 컴포넌트
│ │ ├── header.tsx
│ │ ├── footer.tsx
│ │ ├── sidebar.tsx
│ ├── OptionsDropdown.tsx
│ ├── PromptInput.tsx
│ └── GeneratedImagePreview.tsx
│
├── store/                    # 상태 관리 관련 폴더
│ ├── gallery.ts              # 갤러리 관련 상태 관리
│ ├── auth.ts                 # 인증 관련 상태 관리
│ ├── community.ts            # 커뮤니티 관련 상태 관리
│ └── index.ts                # 상태 관리 유틸리티 및 타입 정의
│
├── hooks/                    # 커스텀 훅 폴더
│ ├── use-toast.ts            # 토스트 관련 훅
│ ├── use-auth.ts             # 인증 관련 훅
│ └── use-media.ts            # 미디어 쿼리 등 UI 관련 훅
│
├── db/                       # 데이터베이스 관련 폴더
│ ├── schema.ts               # DrizzleORM 스키마 정의 파일
│ └── index.ts                # 데이터베이스 연결 초기화 파일
│
├── drizzle/                  # DrizzleORM 관련 설정 파일
│
├── public/                   # 정적 파일 (이미지, 폰트 등)
│ └── favicon.ico
│
├── styles/                   # 글로벌 스타일 (CSS, SCSS, Tailwind 등)
│ └── globals.css
│
├── types/                    # 공통 인터페이스 및 타입 정의
│ └── index.ts                # 여러 파일에서 사용할 공통 타입 및 인터페이스 정의 파일
│
├── utils/                    # 유틸리티 함수 모음
│ ├── fetcher.ts              # API 호출 등 유틸리티 함수
│ └── mockData.ts             # 목업 데이터 관리
│
├── middleware.ts             # 미들웨어 설정 파일
├── .env                      # 환경 변수 설정 파일
├── drizzle.config.ts         # DrizzleORM 설정 파일
├── next.config.mjs           # Next.js 설정 파일
├── package.json              # 프로젝트 패키지 정보
└── tsconfig.json             # TypeScript 설정 파일

```

---

## TypeScript 사용: TS 사용 권장

-   **프로젝트 전반에 TypeScript를 사용하세요.**
-   **타입 안정성을 위해 모든 컴포넌트와 서버 로직에 TypeScript를 적용하세요.**

---

## TypeScript 인터페이스 정의 규칙: 'I' 접두사 사용

-   **인터페이스 정의 시 이름 앞에 'I'를 접두사로 추가하세요.**
-   예시:
    ```typescript
    export interface IComment {
        id: string
        text: string
        author: string
    }
    ```
-   인터페이스 생성은 types/index.ts 파일에 작성하세요.

---

## 컴포넌트 생성: ShadCN 우선 사용

-   **모든 UI 컴포넌트는 ShadCN을 우선으로 생성하세요.**
-   ShadCN 컴포넌트 생성 CLI 명령어는 `npx shadcn@latest add`입니다.
-   **Toast 관련 컴포넌트는 다음 위치에 있습니다:**
    ```
    components/ui/toast.tsx      # Toast 기본 컴포넌트
    components/ui/toaster.tsx    # Toast 컨테이너 컴포넌트
    hooks/use-toast.ts   # Toast 커스텀 훅
    ```

---

## Git 커밋 메시지 작성 규칙

**포맷:**

```
<type>: <subject>

<body>
```

**커밋 타입 (Type):**

-   feat: 새로운 기능 추가
-   fix: 버그 수정
-   docs: 문서 수정
-   style: 코드 포맷팅, 세미콜론 누락, 코드 변경이 없는 경우
-   refactor: 코드 리팩토링
-   test: 테스트 코드, 리팩토링 테스트 코드 추가
-   chore: 빌드 업무 수정, 패키지 매니저 수정

**제목 (Subject):**

-   변경 사항에 대한 간단한 설명
-   50자 이내로 작성
-   마침표 없이 작성
-   현재 시제 사용

**본문 (Body):**

-   변경 사항에 대한 자세한 설명
-   어떻게 보다는 무엇을, 왜 변경했는지 설명
-   여러 줄의 메시지를 작성할 땐 "-"로 구분

**예시:**

```plaintext
feat: 로그인 화면 키보드 UX 개선
- TextInput ref를 사용하여 자동 포커스 기능 추가
- returnKeyType 설정으로 키보드 엔터키 동작 개선
- 전화번호 입력 후 자동으로 비밀번호 입력창으로 포커스 이동
- 비밀번호 입력 후 엔터키로 로그인 가능하도록 개선
```

## Clerk 인증: clerkMiddleware() 사용

-   모든 인증은 Clerk을 사용하세요.
-   middleware.ts 파일에서는 **clerkMiddleware()**를 사용하세요.
-   authMiddleware는 사용하지 않습니다.
-   기본 미들웨어 설정:

    ```typescript
    import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

    const isPublicRoute = createRouteMatcher(['/sign-in(.*)', '/sign-up(.*)'])

    export default clerkMiddleware(async (auth, request) => {
        if (!isPublicRoute(request)) {
            await auth.protect()
        }
    })

    export const config = {
        matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)']
    }
    ```

## ClerkClient: 유저 정보 조회 규칙

-   **ClerkClient를 사용하여 유저 정보를 조회할 때는 다음 규칙을 따르세요:**
-   기본 사용법:

```typescript
import { clerkClient } from '@clerk/nextjs/server'

const client = await clerkClient()

// 단일 유저 조회
const user = await client.users.getUser(userId)

// 다수 유저 조회 (권장)
const users = await client.users.getUserList({
    userId: userIds // string[] 타입
})
```

---

## ORM: Drizzle 사용

-   **데이터베이스 작업을 위해 ORM으로 Drizzle을 사용하세요.**
-   **Drizzle을 사용하여 데이터베이스 모델을 정의하고, CRUD 작업을 구현하세요.**