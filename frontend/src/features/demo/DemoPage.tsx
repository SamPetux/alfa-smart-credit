import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { api } from "../../api/endpoints";
import { isApiError, messageFor } from "../../api/errors";
import { queryKeys } from "../../api/queryClient";
import { useSession } from "../../api/session";
import type { DemoProfile } from "../../api/types";
import { homePathFor } from "../../app/guards";
import { DemoBanner } from "../../app/AppShell";
import { Button, ButtonLink } from "../../components/Button";
import { Field } from "../../components/Field";
import { ErrorBlock, LoadingBlock, Notice } from "../../components/States";

type Intent = "home" | "new";

function ProfileCard({
  profile,
  pending,
  onEnter,
}: {
  profile: DemoProfile;
  pending: Intent | null;
  onEnter: (intent: Intent) => void;
}) {
  const isOfficer = profile.role === "OFFICER";
  return (
    <li className="profile-card">
      <div className="stack-tight">
        <h3>{profile.display_name}</h3>
        <p className="small muted">
          {isOfficer
            ? "Очередь заявок, досье, запрос уточнений и решение по рассчитанной рекомендации."
            : "Подача заявки, черновики, уточнения, предложение и имитация подписи."}
        </p>
      </div>
      <div className="row">
        {isOfficer ? (
          <Button variant="secondary" busy={pending === "home"} busyLabel="Входим…" onClick={() => onEnter("home")}>
            Открыть очередь
          </Button>
        ) : (
          <>
            <Button variant="primary" busy={pending === "new"} busyLabel="Входим…" onClick={() => onEnter("new")}>
              Начать новую заявку
            </Button>
            <Button variant="secondary" busy={pending === "home"} busyLabel="Входим…" onClick={() => onEnter("home")}>
              Мои заявки
            </Button>
          </>
        )}
      </div>
    </li>
  );
}

function PasswordLogin() {
  const { signIn } = useSession();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const info = await signIn(username, password);
      navigate(homePathFor(info.user.role), { replace: true });
    } catch (caught) {
      setError(
        isApiError(caught) && caught.kind === "unauthenticated" ? "Неверное имя пользователя или пароль." : messageFor(caught),
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="panel stack login-form" onSubmit={submit} noValidate>
      <h2>Вход тестовым аккаунтом</h2>
      <p className="small muted">Демовход выключен на этом стенде. Аккаунты описаны в docs/demo-accounts.md.</p>
      <Field label="Имя пользователя" required>
        {(control) => (
          <input
            {...control}
            className="input"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        )}
      </Field>
      <Field label="Пароль" required error={error}>
        {(control) => (
          <input
            {...control}
            className="input"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        )}
      </Field>
      <div>
        <Button type="submit" variant="primary" busy={busy} busyLabel="Входим…" disabled={!username || !password}>
          Войти
        </Button>
      </div>
    </form>
  );
}

export function DemoPage() {
  const { session, switchProfile } = useSession();
  const navigate = useNavigate();
  const [pending, setPending] = useState<{ id: string; intent: Intent } | null>(null);
  const [error, setError] = useState<unknown>(null);
  const profiles = useQuery({ queryKey: queryKeys.demoProfiles, queryFn: ({ signal }) => api.demoProfiles({ signal }) });
  const meta = useQuery({ queryKey: queryKeys.meta, queryFn: ({ signal }) => api.meta({ signal }), staleTime: Infinity });

  async function enter(profile: DemoProfile, intent: Intent) {
    setPending({ id: profile.id, intent });
    setError(null);
    try {
      const info = await switchProfile(profile.id);
      const home = homePathFor(info.user.role);
      navigate(intent === "new" ? "/applications/new" : home, { replace: true });
    } catch (caught) {
      setError(caught);
      setPending(null);
    }
  }

  const demoDisabled = isApiError(profiles.error) && profiles.error.kind === "not_found";
  const clients = profiles.data?.filter((p) => p.role === "CLIENT") ?? [];
  const officers = profiles.data?.filter((p) => p.role === "OFFICER") ?? [];

  return (
    <>
      <a className="skip-link" href="#main">
        К содержимому
      </a>
      <DemoBanner />
      <main className="page page-narrow" id="main" tabIndex={-1}>
        <header className="page-header">
          <span className="brand">
            <span className="brand-mark" aria-hidden="true" />
            <span className="brand-name">Кредитный кабинет</span>
          </span>
          <h1>Вход в демонстрационный стенд</h1>
          <p className="muted">
            Выберите синтетический профиль. Роль и компания определяются сервером по профилю; при смене профиля
            данные прежнего пользователя удаляются из браузера.
          </p>
        </header>

        <div className="stack-lg">
          {meta.data?.privacy_notice ? <Notice tone="warning">{meta.data.privacy_notice}</Notice> : null}

          {session ? (
            <Notice title={`Сейчас открыт профиль: ${session.user.display_name}`}>
              <div className="row">
                <ButtonLink to={homePathFor(session.user.role)} variant="secondary">
                  Продолжить в этом профиле
                </ButtonLink>
              </div>
            </Notice>
          ) : null}

          {error ? <ErrorBlock error={error} title="Не удалось открыть профиль." /> : null}

          {profiles.isPending ? (
            <LoadingBlock rows={4} label="Загружаем демопрофили" />
          ) : demoDisabled ? (
            <PasswordLogin />
          ) : profiles.isError ? (
            <ErrorBlock error={profiles.error} onRetry={() => void profiles.refetch()} />
          ) : (
            <>
              <section className="stack" aria-labelledby="clients-title">
                <h2 id="clients-title">Клиенты — малый бизнес</h2>
                <ul className="profile-grid">
                  {clients.map((profile) => (
                    <ProfileCard
                      key={profile.id}
                      profile={profile}
                      pending={pending?.id === profile.id ? pending.intent : null}
                      onEnter={(intent) => void enter(profile, intent)}
                    />
                  ))}
                </ul>
              </section>
              <section className="stack" aria-labelledby="officers-title">
                <h2 id="officers-title">Сотрудник банка</h2>
                <ul className="profile-grid">
                  {officers.map((profile) => (
                    <ProfileCard
                      key={profile.id}
                      profile={profile}
                      pending={pending?.id === profile.id ? pending.intent : null}
                      onEnter={(intent) => void enter(profile, intent)}
                    />
                  ))}
                </ul>
              </section>
            </>
          )}
        </div>
      </main>
    </>
  );
}
