<div align="center">
  
![AWS Lambda](https://img.icons8.com/color/96/amazon-web-services.png)

# Alertas Automatizados de Expiração de Instâncias Reservadas (EC2/RDS)

**Atualizado: 14 de Janeiro de 2026**

[![Follow @nicoleepaixao](https://img.shields.io/github/followers/nicoleepaixao?label=Follow&style=social)](https://github.com/nicoleepaixao)
[![Star this repo](https://img.shields.io/github/stars/nicoleepaixao/aws-ri-expiration-alert?style=social)](https://github.com/nicoleepaixao/aws-ri-expiration-alert)
[![Medium Article](https://img.shields.io/badge/Medium-12100E?style=for-the-badge&logo=medium&logoColor=white)](https://nicoleepaixao.medium.com/)

<p align="center">
  <a href="README-PT.md">🇧🇷</a>
  <a href="README.md">🇺🇸</a>
</p>

</div>

---

<p align="center">
  <img src="img/aws-reserved-instance-expiration-alert.png" alt="reserved instance alert Architecture" width="2000">
</p>

## **Visão Geral**

Este projeto implementa uma automação FinOps totalmente serverless e de baixo custo que monitora Instâncias Reservadas AWS (EC2 e RDS) e envia alertas quando estão se aproximando da data de expiração. O sistema executa diariamente via AWS Lambda + EventBridge + SNS, avaliando limites de expiração de RI e notificando sua equipe para prevenir aumentos inesperados de custos.

---

## **Como Funciona**

### **Fluxo de Execução**

1. **Gatilho EventBridge:** Regra agendada aciona a função Lambda diariamente
2. **Coleta de Dados:** Lambda consulta todas as Instâncias Reservadas EC2 e RDS ativas
3. **Cálculo de Expiração:** Calcula dias restantes até expiração
4. **Avaliação de Limites:** Verifica contra limites de alerta configurados (60, 30, 7 dias)
5. **Geração de Alerta:** Constrói mensagem de notificação com detalhes do RI
6. **Publicação SNS:** Envia alertas para todos os assinantes registrados
7. **Notificação da Equipe:** Equipes recebem aviso antecipado e podem renovar no prazo

---

## **Componentes Disponíveis**

<div align="center">

| **Componente** | **Tecnologia** | **Propósito** |
|:-------------:|:--------------:|:-----------:|
| **Lambda** | Python 3.12 | Lógica principal de alerta e escaneamento RI |
| **EventBridge** | Cron Schedule | Execução automatizada diária |
| **SNS** | Topic + Subscriptions | Notificações multi-canal |
| **IAM** | Role de Privilégio Mínimo | Execução segura do Lambda |

</div>

---

## **Instruções de Configuração**

### **1. Criar Tópico SNS**

1. **Navegar até Console SNS:** Abra AWS SNS na sua região
2. **Criar Tópico:** Nomeie como `reserved-instance-alert`
3. **Adicionar Assinantes:** Configure email, webhook Slack ou SMS
4. **Confirmar Assinaturas:** Verifique se todos os assinantes aceitam a assinatura

**Nota:** Salve o ARN do Tópico SNS para configuração do Lambda.

---

### **2. Criar Role IAM**

Crie uma role IAM com as seguintes permissões:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeReservedInstances",
        "rds:DescribeReservedDBInstances",
        "sns:Publish",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

**Trust Policy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

---

### **3. Implantar Função Lambda**

1. **Criar Função:**
   - Nome: `reserved-instance-alert`
   - Runtime: Python 3.12
   - Handler: `lambda_function.lambda_handler`
   - Role: Selecione a role IAM criada no passo 2

2. **Upload do Código:** Copie o script Lambda deste repositório

3. **Configurar Variáveis de Ambiente:**

| **Variável** | **Descrição** | **Exemplo** |
|--------------|-----------------|-------------|
| `SNS_TOPIC_ARN` | ARN do tópico SNS | `arn:aws:sns:us-east-1:123456789012:reserved-instance-alert` |
| `REGION` | Região AWS | `us-east-1` |
| `THRESHOLD_DAYS` | Limites de alerta | `60,30,7` |

4. **Testar Função:** Invoque manualmente para verificar se alertas são enviados

---

### **4. Criar Regra EventBridge**

1. **Navegar até EventBridge:** Abra EventBridge Rules
2. **Criar Regra:**
   - Nome: `ri-expiration-daily-check`
   - Tipo de regra: Schedule
   - Expressão cron: `cron(0 12 * * ? *)`
     - Executa todos os dias às 12:00 UTC
3. **Selecionar Alvo:** Escolha a função Lambda criada no passo 3
4. **Ativar Regra:** Habilite o agendamento

---

## **Configuração**

### **Variáveis de Ambiente**

| **Variável** | **Descrição** | **Padrão** |
|--------------|-----------------|-------------|
| `SNS_TOPIC_ARN` | ARN do tópico SNS para notificações | Obrigatório |
| `REGION` | Região AWS para escanear | `us-east-1` |
| `THRESHOLD_DAYS` | Limites de alerta separados por vírgula | `60,30,7` |

### **Exemplo de Mensagem de Alerta**

```text
Alerta de Expiração de Instância Reservada

As seguintes reservas estão se aproximando da expiração:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Serviço: EC2
Tipo de Instância: m5.large
ID da Reserva: abc123
Expira em: 29 dias
Data de Término: 2025-01-12T00:00:00Z

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Serviço: RDS
Tipo de Instância: db.m5.large
ID da Reserva: rds-resv-889
Expira em: 37 dias
Data de Término: 2025-01-20T00:00:00Z

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ação Necessária: Revise e renove estas reservas para manter economia de custos.
```

---

## **Estrutura do Projeto**

```text
.
├── lambda_function.py         # Handler principal do Lambda
├── requirements.txt           # Dependências Python (boto3)
├── iam_policy.json           # Permissões da role IAM
├── README.md                 # Documentação do projeto
└── .gitignore               # Arquivos ignorados
```

---

## **Informações Adicionais**

Para mais detalhes sobre Instâncias Reservadas AWS, otimização de custos e melhores práticas FinOps, consulte:

- [AWS Reserved Instances Documentation](https://aws.amazon.com/ec2/pricing/reserved-instances/) - Guia oficial EC2 RI
- [AWS FinOps Best Practices](https://aws.amazon.com/aws-cost-management/aws-cost-optimization/) - Estratégias de otimização de custos
- [Boto3 EC2 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html) - Referência Python SDK
- [Boto3 RDS Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/rds.html) - Referência API RDS

---

## **Conecte-se & Siga**

Mantenha-se atualizado com estratégias de otimização de custos AWS e automação FinOps:

<div align="center">

[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/nicoleepaixao)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white&style=for-the-badge)](https://www.linkedin.com/in/nicolepaixao/)
[![Medium](https://img.shields.io/badge/Medium-12100E?style=for-the-badge&logo=medium&logoColor=white)](https://medium.com/@nicoleepaixao)

</div>

---

## **Aviso Legal**

Esta ferramenta é fornecida como está para propósitos de monitoramento e alerta. Preços, disponibilidade e políticas de Instâncias Reservadas AWS podem mudar. Sempre verifique detalhes de reserva no Console AWS e consulte documentação oficial da AWS para informações mais atuais. Teste completamente em ambientes de não-produção antes de implantar.

---

<div align="center">

**Otimize seus custos AWS com confiança!**

*Documento Criado: 2 de Dezembro de 2025*

Made with ❤️ by [Nicole Paixão](https://github.com/nicoleepaixao)

</div>
