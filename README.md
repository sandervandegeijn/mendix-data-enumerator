# mendix-data-enumerator

This tool has been co-developed with Frank Spierings: https://github.com/FrankSpierings

This repository contains a tool designed to scan Mendix applications for data that might be exposed publicly. The purpose of this tool is to assist developers and organizations in identifying and mitigating potential data exposure risks within their Mendix applications.

This tool only utilizes the default Mendix APIs, which are publicly documented. The security risks associated with these APIs have been known to Mendix and the community for quite some time. For further reference, please see the Computable article from March 23, 2022 discussing this issue in detail. Mendix has also shared guidelines with their account teams on the existence of this potential problem and how to mitigate it.

## Standalone usage
```
python3 -m venv .
source bin/activate
pip install -r requirements.txt
python mendix-client.py --domain=https://mendixapp.com --proxy=socks5://localhost:8080
```

## Disclaimer

By using this tool, you acknowledge and agree to the following terms:

1.	No Warranty: This tool is provided “as is”, without any warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement. The author and contributors of this tool do not warrant that the tool will be error-free, complete, or up-to-date.
2.	Use at Your Own Risk: The use of this tool is at your own risk. The author and contributors are not responsible for any direct, indirect, incidental, special, exemplary, or consequential damages (including but not limited to procurement of substitute goods or services; loss of use, data, or profits; or business interruption) however caused and on any theory of liability, whether in contract, strict liability, or tort (including negligence or otherwise) arising in any way out of the use of this tool, even if advised of the possibility of such damage.
3.	Compliance with Laws: Users are solely responsible for ensuring that their use of this tool complies with all applicable laws and regulations, including but not limited to data protection laws such as the General Data Protection Regulation (GDPR). Users must not use this tool to scan applications without proper authorization or in any manner that would violate privacy rights or other legal provisions.
4.	Sensitive Data: This tool may identify data that is publicly exposed, some of which may be sensitive. It is the responsibility of the user to handle any such data in accordance with applicable data protection laws and best practices for data security.
