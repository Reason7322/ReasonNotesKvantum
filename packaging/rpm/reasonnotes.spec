%global source_revision cdf63233d2956718e5353ed58ad230dad07aad91
%global debug_package %{nil}

Name:           reasonnotes
Version:        0.1.0
Release:        1.cdf6323%{?dist}
Summary:        Native Qt Widgets offline-first synchronized notes
License:        LicenseRef-Private
URL:            https://github.com/Reason7322/ReasonNotesKvantum
Source0:        %{name}-%{version}.tar.gz
Source1:        reasonnotes
Source2:        org.reasonnotes.ReasonNotesKvantum.desktop

BuildRequires:  gcc
BuildRequires:  python3 >= 3.14
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  wayland-protocols-devel
BuildRequires:  desktop-file-utils
Requires:       python3 >= 3.14
Requires:       python3-pyside6 >= 6.11
Requires:       kvantum
Requires:       qt6-qtwayland
Requires:       kde-connect

%description
ReasonNotes is a private native Qt Widgets note application with explicit,
durably confirmed synchronization through KDE Connect.

%prep
%autosetup

%build
%{python3} scripts/build-wayland-blur.py --target linux-app/native

%install
install -d %{buildroot}%{_libdir}/reasonnotes
cp -a src linux-app %{buildroot}%{_libdir}/reasonnotes/
find %{buildroot}%{_libdir}/reasonnotes -type d -name __pycache__ -prune -exec rm -rf {} +
find %{buildroot}%{_libdir}/reasonnotes -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
printf '%s\n' '%{source_revision}' > %{buildroot}%{_libdir}/reasonnotes/SOURCE_REVISION
install -Dm0755 %{SOURCE1} %{buildroot}%{_bindir}/reasonnotes
install -Dm0644 %{SOURCE2} %{buildroot}%{_datadir}/applications/org.reasonnotes.ReasonNotesKvantum.desktop
install -Dm0644 linux-app/icons/reasonnotes-yamis.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/org.reasonnotes.ReasonNotesKvantum.svg
desktop-file-validate %{buildroot}%{_datadir}/applications/org.reasonnotes.ReasonNotesKvantum.desktop

%files
%defattr(-,root,root,-)
%{_bindir}/reasonnotes
%{_libdir}/reasonnotes/
%{_datadir}/applications/org.reasonnotes.ReasonNotesKvantum.desktop
%{_datadir}/icons/hicolor/scalable/apps/org.reasonnotes.ReasonNotesKvantum.svg

%changelog
* Tue Oct 27 2026 Reason <reason@localhost> - 0.1.0-1.cdf6323
- Package the owner-accepted desktop checkpoint.

