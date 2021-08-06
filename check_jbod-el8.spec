Name:           check_jbod
Version:        0.0.7
%global gittag 0.0.7
Release:        1%{?dist}
Summary:        Nagios script to check the status and fault in Xyratex JBOD.

License:        Apache License 2.0
URL:            https://github.com/guilbaults/%{name}
Source0:        https://github.com/guilbaults/%{name}/archive/v%{gittag}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python36-devel
Requires:       python36
Requires:       sg3_utils

%description
This tool is used to monitor Xyratex JBOD, also known as:

* Seagate/Xyratex SP-2584
* Seagate/Xyratex SP-3584
* Seagate Exos E 4U106
* Dell MD1420
* Lenovo D1212
These JBODs are probably also supported with some slight modifications:
* Dell MD1280
* Lenovo D3284

%prep
%autosetup -n %{name}-%{gittag}
%setup -q

%build

%install
mkdir -p %{buildroot}/usr/lib64/nagios/plugins/

sed -i -e '1i#!/usr/bin/env python3.6' %{name}.py
install -m 0755 %{name}.py %{buildroot}/usr/lib64/nagios/plugins/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%files
/usr/lib64/nagios/plugins/%{name}

%changelog
* Fri Oct 2 2020 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.7-1
- Add support for Lenovo D1212 
* Thu Mar 26 2020 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.6-1
- Ignoring another PSU status flag
* Wed Mar 25 2020 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.5-1
- Increasing fan maximum speed threshold
* Thu Mar 19 2020 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.4-1
- Adjusting threshold for non-idle JBODs
* Thu Mar 19 2020 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.3-1
- Adding other models of JBODs
* Fri Jul 13 2018 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.2-1
- Fixing the shebang and the requirements
* Fri Jul 13 2018 Simon Guilbault <simon.guilbault@calculquebec.ca> 0.0.1-1
- Initial release, supporting Xyratex 84 slots JBOD

