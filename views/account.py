# views/account.py
# Llogaria e klientit: kyçja, regjistrimi me kod verifikimi në email,
# rivendosja e fjalëkalimit dhe dalja. Shfaqet në një dritare të vogël (popover) në header.
import html

import streamlit as st

import auth
import database
import email_service


def _log_in(user: dict) -> None:
    st.session_state.authenticated = True
    st.session_state.current_user = user
    st.query_params["session"] = auth.start_session(user)


def log_out() -> None:
    auth.end_session(st.query_params.get("session"))
    st.query_params.clear()
    st.session_state.authenticated = False
    st.session_state.current_user = None


def _test_code_hint(code: str | None) -> None:
    # Pa SMTP (vetëm gjatë zhvillimit) kodi shfaqet këtu, që të mund të testohet regjistrimi
    if code and not email_service.is_smtp_configured():
        st.info(f"Email-i nuk është konfiguruar. Kodi i testimit: **{code}**")


def _render_verification(pending_email: str) -> None:
    st.markdown('<p class="kpb-pop-title">Verifikoni email-in</p>'
                f'<p class="kpb-pop-sub">Kodi 6-shifror u dërgua te <b>{html.escape(pending_email)}</b></p>',
                unsafe_allow_html=True)
    _test_code_hint(st.session_state.get("pending_verification_code_test"))
    code = st.text_input("Kodi", max_chars=6, key="acc_v_code", placeholder="123456")
    if st.button("Aktivizo llogarinë", key="acc_v_ok", type="primary", use_container_width=True):
        if len(code.strip()) != 6:
            st.warning("Shkruani kodin 6-shifror.")
        else:
            ok, message = auth.verify_client_code(pending_email, code.strip())
            if ok:
                _log_in(database.get_user_by_email(pending_email))
                st.session_state.pending_verification_email = None
                st.session_state.pending_verification_code_test = None
                st.rerun()
            else:
                st.error(message)
    resend_column, back_column = st.columns(2)
    if resend_column.button("Ridërgo kodin", key="acc_v_resend", use_container_width=True):
        sent, message, new_code = auth.resend_client_code(pending_email)
        st.session_state.pending_verification_code_test = new_code
        if sent:
            st.success("Kodi i ri u dërgua.")
        else:
            st.warning(message)
    if back_column.button("Kthehu", key="acc_v_back", use_container_width=True):
        st.session_state.pending_verification_email = None
        st.session_state.pending_verification_code_test = None
        st.rerun()


def _render_login_tab() -> None:
    identifier = st.text_input("Email-i", key="acc_l_id", placeholder="emri@gmail.com")
    password = st.text_input("Fjalëkalimi", type="password", key="acc_l_pw")
    if st.button("Hyr", key="acc_l_ok", type="primary", use_container_width=True):
        if not identifier or not password:
            st.warning("Plotësoni email-in dhe fjalëkalimin.")
            return
        ok, result = auth.login_user(identifier, password)
        if ok:
            _log_in(result)
            st.rerun()
        elif isinstance(result, str) and result.startswith("UNVERIFIED:"):
            st.session_state.pending_verification_email = result.split(":", 1)[1]
            st.rerun()
        else:
            st.error(result)


def _render_register_tab() -> None:
    name = st.text_input("Emri dhe mbiemri", key="acc_r_name", max_chars=80)
    email = st.text_input("Email-i", key="acc_r_email", max_chars=120)
    password = st.text_input("Fjalëkalimi", type="password", key="acc_r_pw", placeholder="Të paktën 6 karaktere")
    confirm = st.text_input("Konfirmo fjalëkalimin", type="password", key="acc_r_pw2")
    if st.button("Krijo llogarinë", key="acc_r_ok", type="primary", use_container_width=True):
        ok, message, code = auth.register_client(name, email, password, confirm)
        if ok:
            st.session_state.pending_verification_email = email.strip().lower()
            st.session_state.pending_verification_code_test = code
            st.rerun()
        else:
            st.error(message)


def _render_reset_tab() -> None:
    if not st.session_state.get("acc_reset_target"):
        identifier = st.text_input("Email-i i llogarisë", key="acc_p_id")
        if st.button("Dërgo kodin", key="acc_p_send", type="primary", use_container_width=True):
            ok, message, target_email, code = auth.request_password_reset_code(identifier)
            if ok:
                st.session_state.acc_reset_target = identifier
                st.session_state.acc_reset_code_test = code
                st.rerun()
            else:
                st.error(message)
        return
    st.caption(f"Kodi u dërgua për: {st.session_state.acc_reset_target}")
    _test_code_hint(st.session_state.get("acc_reset_code_test"))
    code = st.text_input("Kodi 6-shifror", max_chars=6, key="acc_p_code")
    new_password = st.text_input("Fjalëkalimi i ri", type="password", key="acc_p_new")
    confirm = st.text_input("Konfirmo fjalëkalimin", type="password", key="acc_p_new2")
    if st.button("Ruaj fjalëkalimin", key="acc_p_ok", type="primary", use_container_width=True):
        ok, message = auth.confirm_password_reset_code(st.session_state.acc_reset_target, code, new_password, confirm)
        if ok:
            st.session_state.acc_reset_target = None
            st.success(message)
        else:
            st.error(message)
    if st.button("Kthehu", key="acc_p_back", use_container_width=True):
        st.session_state.acc_reset_target = None
        st.rerun()


def render_account_menu() -> None:
    """Përmbajtja e popover-it 'Llogaria' në header."""
    user = st.session_state.get("current_user")
    if st.session_state.get("authenticated") and user:
        name = html.escape(user.get("full_name") or user.get("username") or "")
        st.markdown(f'<p class="kpb-pop-title">Përshëndetje, {name}</p>'
                    f'<p class="kpb-pop-sub">{html.escape(user.get("email") or "")}</p>', unsafe_allow_html=True)
        if user.get("role") == "admin":
            st.caption("Paneli i administratorit hapet me Hap_Admin.bat.")
        if st.button("Dil nga llogaria", key="acc_logout", use_container_width=True):
            log_out()
            st.rerun()
        return

    pending_email = st.session_state.get("pending_verification_email")
    if pending_email:
        _render_verification(pending_email)
        return

    st.markdown('<p class="kpb-pop-title">Llogaria juaj</p>'
                '<p class="kpb-pop-sub">Kyçuni për blerje më të shpejta.</p>', unsafe_allow_html=True)
    login_tab, register_tab, reset_tab = st.tabs(["Hyr", "Regjistrohu", "Fjalëkalimi"])
    with login_tab:
        _render_login_tab()
    with register_tab:
        _render_register_tab()
    with reset_tab:
        _render_reset_tab()
