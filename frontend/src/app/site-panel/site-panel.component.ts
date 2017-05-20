import { Component, Input } from "@angular/core";
import { CampSite } from "../models";
import { ShowboxComponent } from "../showbox";

/**
 * Component to display a single CampSite.
 */
@Component({
    selector: 'site-panel',
    providers: [ShowboxComponent],
    styleUrls: ['./site-panel.component.css'],
    templateUrl: './site-panel.component.html'
})
export class SitePanelComponent {

    @Input() public campsite: CampSite;
}
