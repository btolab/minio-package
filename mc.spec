## Disable debug packages.
%define         debug_package %{nil}

## version from head
%define         gittag %(echo "$(git for-each-ref refs/tags --sort=-taggerdate --format='%%(refname)' --count=1)" | sed 's/^refs\\/tags\\///')
%define         gitver %(echo "$(git describe --tags --long)" | sed -r -e 's/.*([0-9]{4})-0?([0-9]+)-0?([0-9]+)T..-..-..Z-([0-9]+)-g(.*)$/\\1.\\2.\\3/')
%define         gitrel %(echo "$(git describe --tags --long)" | sed -r -e 's/.*([0-9]{4})-0?([0-9]+)-0?([0-9]+)T..-..-..Z-([0-9]+)-g(.*)$/\\4/' | awk '{print $0+1}')
%define         commitid  %(echo "$(git describe --tags --long --abbrev=42)" | sed -r -e 's/.*([0-9]{4})-0?([0-9]+)-0?([0-9]+)T..-..-..Z-([0-9]+)-g(.*)$/\\5/')

%define use_systemd (0%{?fedora} && 0%{?fedora} >= 18) || (0%{?rhel} && 0%{?rhel} >= 7) || (0%{?suse_version} && 0%{?suse_version} >=1210)

Summary:        S3 compatible command-line client
Name:           minio-client
Version:        %{gitver}
Release:        %{gitrel}.nmi
Vendor:         MinIO, Inc.
License:        Apache v2.0
Group:          Applications/File
Source0:        https://github.com/minio/mc/archive/%{commitid}.tar.gz
URL:            https://www.min.io/
BuildRequires:  golang >= 1.13

BuildRoot:      %{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
MinIO Client (mc) provides a modern alternative to UNIX commands like ls, cat,
cp, mirror, diff, find etc. It supports filesystems and Amazon S3 compatible
cloud storage service (AWS Signature v2 and v4).

%prep
%setup -q -n mc-%{commitid}

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

%install
rm -rf %{buildroot}
%{__install} -m 0755 -vd %{buildroot}%{_bindir}
%{__install} -m 0755 -vp mc %{buildroot}%{_bindir}

%clean
rm -rf $RPM_BUILD_ROOT

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%files
%defattr(644,root,root,755)
%license LICENSE
%doc README.md docs
%attr(755, root, root) %{_bindir}/mc
