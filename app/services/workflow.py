"""Main workflow orchestration service."""

import structlog
from datetime import datetime

from app.models.workflow import WorkflowContext, WorkflowStatus
from app.clients.salesforce import SalesforceClient
from app.clients.ada import AdaClient
from app.clients.openai_client import OpenAIClient
from app.clients.slack import SlackClient
from app.services.content_generator import ContentGenerator
from app.services.knowledge_builder import KnowledgeBuilder
from app.services.agent_builder import AgentBuilder

logger = structlog.get_logger()


class WorkflowOrchestrator:
    """
    Orchestrates the complete Ada agent provisioning workflow.

    Workflow steps mirror the Zapier automation:
    1. Retrieve Salesforce data (Opportunity, Account, Partner)
    2. Filter for new customers only
    3. Notify Slack
    4. Generate company description (OpenAI)
    5. Create knowledge sources and articles
    6. Generate TK questions
    7. Build endpoints
    8. Create channel and conversation flows
    9. Notify SC team with completion
    """

    def __init__(self):
        """Initialize workflow with API clients."""
        self.sf_client = SalesforceClient()
        self.ada_client = AdaClient()
        self.openai_client = OpenAIClient()
        self.slack_client = SlackClient()

        self.content_generator = ContentGenerator(self.openai_client)
        self.knowledge_builder = KnowledgeBuilder(self.ada_client, self.openai_client)
        self.agent_builder = AgentBuilder(self.ada_client, self.openai_client)

    async def execute(self, opportunity_id: str, workflow_id: str) -> WorkflowStatus:
        """
        Execute the complete provisioning workflow.

        Args:
            opportunity_id: Salesforce Opportunity ID
            workflow_id: Unique workflow identifier for tracking

        Returns:
            Final workflow status

        Raises:
            Exception: Any unhandled errors during workflow execution
        """
        logger.info(
            "workflow_started",
            workflow_id=workflow_id,
            opportunity_id=opportunity_id
        )

        # Initialize workflow context
        context = WorkflowContext(
            workflow_id=workflow_id,
            opportunity_id=opportunity_id
        )

        status = WorkflowStatus(
            workflow_id=workflow_id,
            status="in_progress",
            opportunity_id=opportunity_id,
            started_at=datetime.utcnow()
        )

        try:
            # Step 1-6: Retrieve and validate Salesforce data
            await self._retrieve_salesforce_data(context, status)

            # Step 7: Notify Slack - workflow started
            await self._notify_workflow_start(context)

            # Step 12-17: Build knowledge base
            await self._build_knowledge_base(context, status)

            # Step 18-23: Build endpoints
            await self._build_endpoints(context, status)

            # Step 24-28: Create channels and conversations
            await self._setup_channels_conversations(context, status)

            # Step 29-31: Finalize and notify completion
            await self._finalize_workflow(context, status)

            # Mark as completed
            status.status = "completed"
            status.completed_at = datetime.utcnow()

            logger.info(
                "workflow_completed",
                workflow_id=workflow_id,
                duration_seconds=(status.completed_at - status.started_at).total_seconds()
            )

        except Exception as e:
            status.status = "failed"
            status.error = str(e)
            status.completed_at = datetime.utcnow()

            logger.error(
                "workflow_failed",
                workflow_id=workflow_id,
                opportunity_id=opportunity_id,
                error=str(e),
                exc_info=True
            )

            # Notify Slack of failure
            await self.slack_client.send_error_notification(
                workflow_id=workflow_id,
                opportunity_id=opportunity_id,
                error=str(e)
            )

            raise

        return status

    async def _retrieve_salesforce_data(
        self,
        context: WorkflowContext,
        status: WorkflowStatus
    ) -> None:
        """
        Steps 1-6: Retrieve Salesforce data and filter.

        - Get Opportunity info
        - Filter for new customers only
        - Get Account name
        - Get Partner/Consultant info
        """
        status.current_step = "retrieve_salesforce_data"
        logger.info("step_started", step="retrieve_salesforce_data")

        # TODO: Implement actual Salesforce queries
        # This requires the field names from the Zapier export

        # Placeholder implementation:
        # opp = await self.sf_client.get_opportunity(context.opportunity_id)
        # context.account_id = opp["AccountId"]
        # context.is_new_customer = opp["Type"] == "New Customer"

        # if not context.is_new_customer:
        #     raise ValueError("Opportunity is not for a new customer - workflow terminated")

        # account = await self.sf_client.get_account(context.account_id)
        # context.account_name = account["Name"]

        # partner = await self.sf_client.get_partner(opp["PartnerId"])
        # context.partner_name = partner["Name"]

        status.steps_completed.append("retrieve_salesforce_data")
        logger.info("step_completed", step="retrieve_salesforce_data")

    async def _notify_workflow_start(self, context: WorkflowContext) -> None:
        """Step 7: Notify Slack that workflow has started."""
        logger.info("step_started", step="notify_workflow_start")

        await self.slack_client.send_workflow_start_notification(
            account_name=context.account_name or "Unknown",
            opportunity_id=context.opportunity_id,
            workflow_id=context.workflow_id
        )

        logger.info("step_completed", step="notify_workflow_start")

    async def _build_knowledge_base(
        self,
        context: WorkflowContext,
        status: WorkflowStatus
    ) -> None:
        """
        Steps 12-17: Build knowledge base.

        - Create knowledge source in Ada
        - Generate company description (OpenAI)
        - Generate knowledge articles (OpenAI)
        - Upload articles to Ada
        """
        status.current_step = "build_knowledge_base"
        logger.info("step_started", step="build_knowledge_base")

        # TODO: Implement knowledge base building
        # This requires the OpenAI prompts from Zapier steps 15, 16

        # Placeholder:
        # context.company_description = await self.content_generator.generate_company_description(
        #     account_name=context.account_name
        # )

        # context.knowledge_articles = await self.content_generator.generate_knowledge_articles(
        #     company_description=context.company_description
        # )

        # context.knowledge_source_id = await self.knowledge_builder.create_knowledge_source(
        #     account_name=context.account_name,
        #     articles=context.knowledge_articles
        # )

        status.steps_completed.append("build_knowledge_base")
        logger.info("step_completed", step="build_knowledge_base")

    async def _build_endpoints(
        self,
        context: WorkflowContext,
        status: WorkflowStatus
    ) -> None:
        """
        Steps 18-23: Build endpoints.

        - Scale TK questions (OpenAI)
        - Convert TK questions
        - Build endpoints (OpenAI)
        - Create endpoints in Ada
        """
        status.current_step = "build_endpoints"
        logger.info("step_started", step="build_endpoints")

        # TODO: Implement endpoint building
        # Requires OpenAI prompts from steps 18, 20
        # Requires Ada API calls from steps 22, 23

        status.steps_completed.append("build_endpoints")
        logger.info("step_completed", step="build_endpoints")

    async def _setup_channels_conversations(
        self,
        context: WorkflowContext,
        status: WorkflowStatus
    ) -> None:
        """
        Steps 24-28: Create channels and conversation flows.

        - Create channel in Ada
        - Setup conversation instructions
        - Create message templates
        """
        status.current_step = "setup_channels_conversations"
        logger.info("step_started", step="setup_channels_conversations")

        # TODO: Implement channel and conversation setup
        # Requires Ada API details from steps 24-27

        status.steps_completed.append("setup_channels_conversations")
        logger.info("step_completed", step="setup_channels_conversations")

    async def _finalize_workflow(
        self,
        context: WorkflowContext,
        status: WorkflowStatus
    ) -> None:
        """
        Steps 29-31: Finalize and notify completion.

        - Send final prompt (OpenAI)
        - Generate CLI commands for SC team
        - Notify Slack with completion details
        """
        status.current_step = "finalize_workflow"
        logger.info("step_started", step="finalize_workflow")

        # TODO: Implement finalization
        # Requires OpenAI prompt from step 29
        # Requires JS code from step 30
        # Requires Slack message from step 31

        await self.slack_client.send_completion_notification(
            account_name=context.account_name or "Unknown",
            workflow_id=context.workflow_id,
            agent_url=f"https://ada.cx/agents/{context.channel_id}"  # Placeholder
        )

        status.steps_completed.append("finalize_workflow")
        logger.info("step_completed", step="finalize_workflow")
