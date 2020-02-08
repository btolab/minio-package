## Disable debug packages.
%define         debug_package %{nil}

## version from head
%define         gittag %(echo "$(git for-each-ref refs/tags --sort=-taggerdate --format='%%(refname)' --count=1)" | sed 's/^refs\\/tags\\///')
%define         gitver %(echo "$(git describe --tags --long)" | sed -r -e 's/.*([0-9]{4})-0?([0-9]+)-0?([0-9]+)T..-..-..Z-([0-9]+)-g(.*)$/\\1.\\2.\\3/')
%define         gitrel %(echo "$(git describe --tags --long)" | sed -r -e 's/.*([0-9]{4})-0?([0-9]+)-0?([0-9]+)T..-..-..Z-([0-9]+)-g(.*)$/\\4/' | awk '{print $0+1}')
%define         commitid  %(echo "$(git describe --tags --long --abbrev=42)" | sed -r -e 's/.*([0-9]{4})-0?([0-9]+)-0?([0-9]+)T..-..-..Z-([0-9]+)-g(.*)$/\\5/')

%define use_systemd (0%{?fedora} && 0%{?fedora} >= 18) || (0%{?rhel} && 0%{?rhel} >= 7) || (0%{?suse_version} && 0%{?suse_version} >=1210)

Summary:        Cloud Storage Server.
Name:           minio
Version:        %{gitver}
Release:        %{gitrel}%{?dist}.nmi
Vendor:         MinIO, Inc.
License:        Apache v2.0
Group:          Applications/File
Source0:        https://github.com/minio/minio/archive/%{commitid}.tar.gz
Source1:        %{name}.service
URL:            https://www.min.io/
Requires(pre):  shadow-utils
BuildRequires:  golang >= 1.7

%if %{use_systemd}
BuildRequires:  systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
%endif

BuildRoot:      %{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
MinIO is an object storage server released under Apache License v2.0.
It is compatible with Amazon S3 cloud storage service. It is best
suited for storing unstructured data such as photos, videos, log
files, backups and container / VM images. Size of an object can
range from a few KBs to a maximum of 5TiB.

%prep
%setup -q -n %{name}-%{commitid}

%build
# setup flags like 'go run buildscripts/gen-ldflags.go' would do
scommitid=$(echo %{commitid} | cut -c1-12)

LDFLAGS="
-X $prefix.Version=%{version}-%{gitrel}
-X $prefix.ReleaseTag=%{gittag}
-X $prefix.CommitID=%{commitid}
-X $prefix.ShortCommitID=$scommitid
"
make

%{__cat} <<'EOF' > "%{_builddir}/%{?buildsubdir}/%{name}.sysconf"
# Remote volumes to be used for Minio server.
#MINIO_VOLUMES=http://node1/var/minio/data http://node2/var/minio/data http://node3/var/minio/data http://node4/var/minio/data

# Access Key of the server.
#MINIO_ACCESS_KEY=Server-Access-Key

# Secret key of the server.
#MINIO_SECRET_KEY=Server-Secret-Key

# Use if you want to run Minio on a custom port.
#MINIO_OPTS="--address :9199"
EOF

%install
rm -rf %{buildroot}
%{__install} -m 0755 -vd %{buildroot}%{_bindir}
%{__install} -m 0755 -vp %{name} %{buildroot}%{_bindir}
%{__install} -m 0750 -vd %{buildroot}%{_sharedstatedir}/%{name}
%{__install} -vd %{buildroot}%{_sysconfdir}/sysconfig
%{__install} -v "%{_builddir}/%{?buildsubdir}/%{name}.sysconf" %{buildroot}%{_sysconfdir}/sysconfig/%{name}

%if %{use_systemd}
%{__install} -vd %{buildroot}%{_unitdir}
%{__install} -v %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || useradd -r -g %{name} \
    -d %{_sharedstatedir}/%{name} -s /sbin/nologin \
    -c "%{name} user" %{name}

%post
%if %{use_systemd}
%systemd_post %{name}.service
%endif

%preun
%if %{use_systemd}
%systemd_preun %{name}.service
%endif

%postun
%if %{use_systemd}
%systemd_postun %{name}.service
%endif

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%files
%defattr(644,root,root,755)
%license LICENSE
%doc README.md SECURITY.md docs
%attr(640, root, %{name}) %config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%attr(755, root, root) %{_bindir}/minio
%attr(-, %{name}, %{name}) %{_sharedstatedir}/%{name}
%if %{use_systemd}
%config %{_unitdir}/%{name}.service
%endif
